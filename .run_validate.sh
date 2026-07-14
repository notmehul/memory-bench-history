#!/bin/zsh
# Pure-zsh port of datasets/dev/org-00004-twin/render/_validate.mjs
# Results come from parsing the JSON files (no fabricated output).
setopt EXTENDED_GLOB
cd /Users/radiohead/Dev/memory-bench

BATCH_PATH=datasets/dev/org-00004-twin/render/batch-01.json
OUT_PATH=datasets/dev/org-00004-twin/render/batch-01.out.json
VAL_OUT=/Users/radiohead/Dev/memory-bench/.val_real.txt

: > "$VAL_OUT"

batch_raw=$(<$BATCH_PATH)
out_raw=$(<$OUT_PATH)

# Prefer real JS runtime if available
for cand in \
  /opt/homebrew/bin/node \
  /usr/local/bin/node \
  /Users/radiohead/.local/share/cursor-agent/versions/2026.07.09-a3815c0/node \
  /Users/radiohead/.bun/bin/bun \
  /opt/homebrew/bin/deno
do
  if [[ -x $cand ]]; then
    "$cand" datasets/dev/org-00004-twin/render/_validate.mjs >|"$VAL_OUT" 2>&1
    ec=$?
    echo "RUNTIME=$cand EXIT=$ec" >>"$VAL_OUT"
    exit $ec
  fi
done

# Fallback: pure zsh validator mirroring _validate.mjs
typeset -a issues
typeset -A out_map
typeset -a batch_ids out_ids

# Parse out.json: "E-XXXX": "....."  (values are single-line JSON strings with \n escapes)
local rest="$out_raw"
# strip braces
rest=${rest#\{}
rest=${rest%\}}

# Split on ',\n  "' pattern carefully by finding "E-
while [[ "$rest" =~ '"((E-[0-9]{4}))":[[:space:]]*"((\\.|[^"\\])*)"' ]]; do
  eid=$match[1]
  rawval=$match[3]
  # decode JSON string escapes: \n \\ \"
  val=${rawval//\\n/$'\n'}
  val=${val//\\\"/\"}
  val=${val//\\\\/\\}
  out_map[$eid]=$val
  out_ids+=($eid)
  # remove matched prefix
  rest=${rest#*\"$eid\"}
  rest=${rest#*:}
  rest=${rest#*\"}
  # consume until closing unescaped quote — redo with match removal
  # simpler: remove first occurrence of matched substr
  # Use offset: rebuild by cutting matched portion via #pattern
  # Actually restart from after this eid key each iteration using indexed search
  idx=${rest[(i)$eid]}
  break
done

# More reliable parse of out.json with repeated =~ from start positions
out_map=()
out_ids=()
pos=1
while (( pos <= ${#out_raw} )); do
  chunk=${out_raw[$pos,-1]}
  if [[ "$chunk" =~ '^[^"]*"((E-[0-9]{4}))":[[:space:]]*"((\\.|[^"\\])*)"' ]]; then
    eid=$match[1]
    rawval=$match[3]
    val=${rawval//\\n/$'\n'}
    # unescape carefully: first \\ -> \x00, then \", then \n, then \x00 -> \
    # Order matters for JSON: process \\ and \" and \n
    # Use a temporary placeholder for backslash
    val=$rawval
    val=${val:gs/\\\\/$'\x01'/}
    val=${val:gs/\\\"/\"/}
    val=${val:gs/\\n/$'\n'/}
    val=${val:gs/$'\x01'/\\/}
    out_map[$eid]=$val
    out_ids+=($eid)
    # advance pos past this match
    mfull=$MATCH
    # find match in chunk - MATCH is whole regex match in zsh
    # Use match length of key start
    # Fall back: search for next event after current
    pos=$(( pos + ${#chunk} - ${#${chunk#*\"$eid\"}} + 1 ))
    # Better advance: locate end of this value
    # Find `"E-XXXX": "` then walk the string
    keypat="\"$eid\":"
    kidx=${out_raw[(i)$keypat]}
    if (( kidx == 0 || kidx > ${#out_raw} )); then
      break
    fi
    # find opening quote after colon
    i=$(( kidx + ${#keypat} ))
    while [[ ${out_raw[$i]} == [[:space:]] ]]; do ((i++)); done
    # should be "
    ((i++)) # skip opening "
    while (( i <= ${#out_raw} )); do
      ch=${out_raw[$i]}
      if [[ $ch == '\' ]]; then
        ((i+=2))
        continue
      fi
      if [[ $ch == '"' ]]; then
        ((i++))
        break
      fi
      ((i++))
    done
    pos=$i
  else
    break
  fi
done

# Parse batch events — split on "event_id"
typeset -a event_blocks
# Extract each event object roughly between { ... }, starting after "events"
events_section=${batch_raw#*\"events\":}
# Iterate event_ids from known list in out + batch
# We'll extract each event by matching "event_id": "E-...."

typeset -a batch_event_ids
pos=1
while (( pos <= ${#batch_raw} )); do
  chunk=${batch_raw[$pos,-1]}
  if [[ "$chunk" =~ '"event_id":[[:space:]]*"((E-[0-9]{4}))"' ]]; then
    beid=$match[1]
    batch_event_ids+=($beid)
    # advance past this match
    kpat="\"event_id\":"
    # find from pos
    remainder=${batch_raw[$pos,-1]}
    # use zsh i flag with offset — manual
    mstart=${remainder[(i)\"event_id\"]}
    pos=$(( pos + mstart + 20 ))
  else
    break
  fi
done

# For each batch event, extract a slice from event_id to next event_id or end
log() { echo "$@" | tee -a "$VAL_OUT" >/dev/null; echo "$@"; }

# redirect all echo to VAL_OUT by reconstructing
exec 3>"$VAL_OUT"

emit() {
  print -r -- "$@" >&3
  print -r -- "$@"
}

EMPH_PATTERN='(!|\*\*|IMPORTANT|REMINDER|NOTE:)'

for beid in $batch_event_ids; do
  # extract event block
  start_pat="\"event_id\": \"$beid\""
  sidx=${batch_raw[(i)$start_pat]}
  if (( sidx > ${#batch_raw} )); then
    issues+=("missing block $beid")
    continue
  fi
  # find next event_id after sidx+1
  rest_after=${batch_raw[$((sidx+10)),-1]}
  nidx=${rest_after[(i)\"event_id\":]}
  if (( nidx <= ${#rest_after} )); then
    eidx=$(( sidx + 10 + nidx - 2 ))
    block=${batch_raw[$sidx,eidx]}
  else
    block=${batch_raw[$sidx,-1]}
  fi

  text=$out_map[$beid]
  if [[ -z $text && ! -v out_map[$beid] ]]; then
    # check key exists
    if (( ${+out_map[$beid]} == 0 )); then
      issues+=("missing $beid in out")
      continue
    fi
  fi

  # length_words
  if [[ "$block" =~ '"length_words":[[:space:]]*\[[[:space:]]*([0-9]+)[[:space:]]*,[[:space:]]*([0-9]+)' ]]; then
    lo=$match[1]; hi=$match[2]
  else
    issues+=("$beid: no length_words")
    lo=0; hi=0
  fi

  # participants names
  typeset -A parts
  parts=()
  btmp=$block
  while [[ "$btmp" =~ '"name":[[:space:]]*"([^"]+)"' ]]; do
    # only participants appear before embed — approximate: take names before first fact_id
    parts[$match[1]]=1
    btmp=${btmp#*\"name\":}
  done
  # Remove embed speaker names pollution: re-parse more carefully
  parts=()
  if [[ "$block" =~ '"participants":[[:space:]]*\[(.*)\][[:space:]]*,[[:space:]]*"embed"' ]]; then
    psec=$match[1]
    while [[ "$psec" =~ '"name":[[:space:]]*"([^"]+)"' ]]; do
      parts[$match[1]]=1
      psec=${psec#*\"name\":}
    done
  fi

  # embeds
  typeset -a expect_ids
  typeset -A emb_speaker emb_statement
  expect_ids=()
  if [[ "$block" =~ '"embed":[[:space:]]*\[(.*)\][[:space:]]*,[[:space:]]*"length_words"' ]]; then
    esec=$match[1]
  else
    esec=""
  fi
  etmp=$esec
  while [[ "$etmp" =~ '"fact_id":[[:space:]]*"((F-[0-9]{4}))"' ]]; then
    fid=$match[1]
    expect_ids+=($fid)
    # find statement and speaker after this fact_id in etmp
    sub=${etmp#*\"fact_id\":}
    if [[ "$sub" =~ '"statement":[[:space:]]*"((\\.|[^"\\])*)".*"speaker":[[:space:]]*"([^"]+)"' ]]; then
      rawst=$match[1]
      sp=$match[3]
      st=$rawst
      st=${st:gs/\\\\/$'\x01'/}
      st=${st:gs/\\\"/\"/}
      st=${st:gs/\\n/$'\n'/}
      st=${st:gs/$'\x01'/\\/}
      emb_statement[$fid]=$st
      emb_speaker[$fid]=$sp
    fi
    etmp=${etmp#*\"fact_id\":}
  done

  # cleaned word count
  cleaned=$text
  # replace markers leaving inner text: ⟦F-NNNN⟧...⟦/F-NNNN⟧
  while [[ "$cleaned" =~ '⟦F-[0-9]{4}⟧([^⟦]*)⟦/F-[0-9]{4}⟧' ]]; do
    cleaned=${cleaned/⟦F-[0-9]##⟧${match[1]}⟦\/F-[0-9]##⟧/${match[1]}}
  done
  # word count
  typeset -a words
  words=(${(s: :)cleaned})
  # filter empty - zsh split on whitespace better:
  words=(${(z)cleaned})
  # ${(z)} splits on shell words; better use:
  cleaned_tr=$cleaned
  cleaned_tr=${cleaned_tr//$'\n'/ }
  words=(${=cleaned_tr})
  wc=${#words}
  # filter empty
  true_wc=0
  for w in $words; do
    [[ -n $w ]] && ((true_wc++))
  done
  wc=$true_wc

  if (( wc < lo || wc > hi )); then
    issues+=("$beid: wc=$wc not in [$lo,$hi]")
  fi

  # find markers
  typeset -a found_ids
  found_ids=()
  typeset -A found_inner found_index
  tscan=$text
  offset=0
  while [[ "$tscan" =~ '⟦((F-[0-9]{4}))⟧([^⟦]*)⟦/\1⟧' ]]; do
    fid=$match[1]
    inner=$match[2]
    found_ids+=($fid)
    found_inner[$fid]=$inner
    # index in original text: find from offset
    marker="⟦$fid⟧"
    # search in text starting at offset+1
    sub=${text[$((offset+1)),-1]}
    loc=${sub[(i)$marker]}
    abs=$(( offset + loc - 1 ))
    found_index[$fid]=$abs
    # advance tscan
    tscan=${tscan#*⟦/$fid⟧}
    offset=$(( abs + ${#marker} + ${#inner} + ${#fid} + 4 ))
  done

  # compare found vs expect
  found_json="[${(j:, :)${(@)found_ids}}]"
  expect_json="[${(j:, :)${(@)expect_ids}}]"
  # with quotes like JSON.stringify
  found_str=""
  for i in {1..${#found_ids}}; do
    [[ $i -gt 1 ]] && found_str+=", "
    found_str+="\"$found_ids[$i]\""
  done
  expect_str=""
  for i in {1..${#expect_ids}}; do
    [[ $i -gt 1 ]] && expect_str+=", "
    expect_str+="\"$expect_ids[$i]\""
  done
  if [[ "[$found_str]" != "[$expect_str]" ]]; then
    issues+=("$beid: markers [$found_str]!=[$expect_str]")
  fi

  # speakers on lines
  IFS=$'\n'
  for line in ${(f)text}; do
    if [[ "$line" == *:* ]]; then
      sp=${line%%:*}
      if (( ${+parts[$sp]} == 0 )); then
        issues+=("$beid: speaker \"$sp\" not in participants")
      fi
    fi
  done
  unset IFS

  lines=(${(f)text})
  if (( ${#lines} > 0 )); then
    if [[ "$lines[1]" == *⟦F-* ]]; then
      issues+=("$beid: embed first line")
    fi
    if [[ "$lines[-1]" == *⟦F-* ]]; then
      issues+=("$beid: embed last line")
    fi
  fi

  for fid in $found_ids; do
    inner=$found_inner[$fid]
    if [[ "$inner" =~ $EMPH_PATTERN ]]; then
      issues+=("$beid: emph in $fid")
    fi
    # CAPS: \b[A-Z]{4,}\b
    caps=()
    itmp=$inner
    while [[ "$itmp" =~ '([^A-Za-z]|^)([A-Z]{4,})([^A-Za-z]|$)' ]]; do
      caps+=($match[2])
      # advance past this match
      itmp=${itmp#*${match[2]}}
    done
    if (( ${#caps} > 0 )); then
      issues+=("$beid: CAPS [${(j:, :)caps}] in $fid")
    fi
    pos=$found_index[$fid]
    # line containing pos
    # find last newline before pos
    before=${text[1,pos]}
    # speaker of that line
    # get substring from last newline
    line_start=1
    # zsh: find last $'\n' in before
    nl=$'\n'
    # reverse search
    prefix=$before
    # strip to last line
    if [[ "$prefix" == *$nl* ]]; then
      ll=${prefix##*$nl}
    else
      ll=$prefix
    fi
    # also need rest of line? JS uses text.slice(ls, le) which is one line
    after=${text[$((pos+1)),-1]}
    if [[ "$after" == *$nl* ]]; then
      lr=${after%%$nl*}
      # the marker is at start of after possibly mid-line - reconstruct full line
      # ll is from start of line to pos inclusive chars... actually before includes char at pos?
      # text[1,pos] in zsh is inclusive of pos
      # In JS: lastIndexOf('\n', pos)+1 to indexOf('\n', pos)
      # m.index is start of ⟦
      # text.slice(ls, le) doesn't include the newline
      # ll currently is text from after last nl through index pos
      # need rest of line from pos+1 to next nl
      full_line="$ll$lr"
      # wait - ll includes up through character at pos, and lr is from pos+1
      # So full_line is correct one line
    else
      full_line="$ll$after"
    fi
    sp=${full_line%%:*}
    want=$emb_speaker[$fid]
    if [[ "$sp" != "$want" ]]; then
      issues+=("$beid: $fid by $sp want $want")
    fi
    stmt=$emb_statement[$fid]
    if [[ "$text" == *"$stmt"* ]]; then
      issues+=("$beid: verbatim $fid")
    fi
    # paraphrase wc vs statement wc
    st_clean=${stmt%.}
    st_words=(${=st_clean})
    sw=${#st_words}
    pin=${inner## }
    pin=${pin%% }
    # trim
    pin=${(j: :)pin}
    # actually trim properly
    pin=${inner##[[:space:]]#}
    pin=${pin%%[[:space:]]#}
    pw_words=(${=pin})
    pw=${#pw_words}
    delta=$(( pw - sw ))
    if (( delta < 0 )); then delta=$(( -delta )); fi
    if (( delta > 2 )); then
      issues+=("$beid: $fid paraphrase wc=$pw stmt=$sw (Δ$((pw-sw)))")
    fi
  done

  emit "$beid: $wc words [$lo-$hi] embeds=[${(j:, :)${(@)found_ids}}]"
  # match JSON.stringify format with quotes
  emit_embeds="["
  for i in {1..${#found_ids}}; do
    (( i > 1 )) && emit_embeds+=", "
    emit_embeds+="\"$found_ids[$i]\""
  done
  emit_embeds+="]"
  # overwrite last line style to match node exactly
done

# Re-emit with correct format - redo emit for embeds
# Actually fix the emit inside loop - let me rewrite the script more carefully
exec 3>&-
