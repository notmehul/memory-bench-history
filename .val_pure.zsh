# pure-zsh validator — paste body only; no shebang execution needed
# mirrors _validate.mjs logic while parsing batch-01.json + batch-01.out.json

setopt RE_MATCH_PCRE 2>/dev/null || true

ROOT=/Users/radiohead/Dev/memory-bench
BATCH=$ROOT/datasets/dev/org-00004-twin/render/batch-01.json
OUTF=$ROOT/datasets/dev/org-00004-twin/render/batch-01.out.json
VAL=$ROOT/.val_real.txt
: > $VAL

batch=$(<$BATCH)
out=$(<$OUTF)

typeset -A OUT
typeset -a OUT_IDS BATCH_IDS

# --- parse out.json ---
pos=1
olen=${#out}
while (( pos <= olen )); do
  chunk=${out[$pos,olen]}
  if [[ ! "$chunk" =~ '"((E-[0-9]{4}))":[[:space:]]*"' ]]; then
    break
  fi
  eid=${match[1]}
  # find absolute start of value opening quote
  prefix_pat="\"${eid}\""
  # locate from pos
  local_chunk=$chunk
  # match[0]/ MATCH in zsh without PCRE is whole match — find eid occurrence
  # Walk: find "E-XXXX": then whitespace then "
  search=$chunk
  # Use pattern removal to find end of key
  # Absolute index of key:
  key="\"$eid\""
  # search within out from pos
  found_at=0
  i=$pos
  keylen=${#key}
  while (( i <= olen - keylen + 1 )); do
    if [[ ${out[$i,$((i+keylen-1))]} == "$key" ]]; then
      found_at=$i
      break
    fi
    ((i++))
  done
  if (( found_at == 0 )); then
    break
  fi
  j=$((found_at + keylen))
  while [[ ${out[$j]} == [[:space:]] || ${out[$j]} == ':' ]]; do
    ((j++))
  done
  # out[j] should be opening quote
  if [[ ${out[$j]} != '"' ]]; then
    echo "PARSE ERR at $eid" >>$VAL
    break
  fi
  ((j++))
  raw=""
  while (( j <= olen )); do
    ch=${out[$j]}
    if [[ $ch == '\' ]]; then
      nxt=${out[$((j+1))]}
      raw+="\\$nxt"
      ((j+=2))
      continue
    fi
    if [[ $ch == '"' ]]; then
      ((j++))
      break
    fi
    raw+="$ch"
    ((j++))
  done
  # unescape JSON string
  val=""
  k=1
  rlen=${#raw}
  while (( k <= rlen )); do
    ch=${raw[$k]}
    if [[ $ch == '\' && k < rlen ]]; then
      nxt=${raw[$((k+1))]}
      case $nxt in
        n) val+=$'\n' ;;
        t) val+=$'\t' ;;
        \") val+='"' ;;
        \\) val+='\\' ;;
        *) val+="$nxt" ;;
      esac
      ((k+=2))
    else
      val+="$ch"
      ((k++))
    fi
  done
  OUT[$eid]=$val
  OUT_IDS+=($eid)
  pos=$j
done

# --- parse batch event_ids in order ---
pos=1
blen=${#batch}
while (( pos <= blen )); do
  chunk=${batch[$pos,blen]}
  if [[ ! "$chunk" =~ '"event_id":[[:space:]]*"((E-[0-9]{4}))"' ]]; then
    break
  fi
  beid=${match[1]}
  BATCH_IDS+=($beid)
  # advance past this event_id occurrence
  key="\"event_id\""
  i=$pos
  while (( i <= blen )); do
    if [[ ${batch[$i,$((i+10))]} == '"event_id"' ]]; then
      # verify it's this id
      rest=${batch[$i,$((i+40))]}
      if [[ "$rest" == *"$beid"* ]]; then
        pos=$((i + 20))
        break
      fi
    fi
    ((i++))
  done
  if (( i > blen )); then
    break
  fi
done

typeset -a ISSUES

# missing / extra
typeset -A batch_set out_set
for id in $BATCH_IDS; do batch_set[$id]=1; done
for id in $OUT_IDS; do out_set[$id]=1; done
miss=(); ext=()
for id in $BATCH_IDS; do
  (( ${+out_set[$id]} )) || miss+=($id)
done
for id in $OUT_IDS; do
  (( ${+batch_set[$id]} )) || ext+=($id)
done
if (( ${#miss} )); then ISSUES+=("missing ${miss[*]}"); fi
if (( ${#ext} )); then ISSUES+=("extra ${ext[*]}"); fi

json_arr() {
  # build JSON array of strings from $@
  local s="["
  local i=1
  local n=$#
  local a
  for a in "$@"; do
    (( i > 1 )) && s+=", "
    s+="\"$a\""
    ((i++))
  done
  s+="]"
  print -r -- "$s"
}

for beid in $BATCH_IDS; do
  # extract block
  start_key="\"event_id\": \"$beid\""
  sidx=0
  i=1
  sklen=${#start_key}
  while (( i <= blen - sklen + 1 )); do
    if [[ ${batch[$i,$((i+sklen-1))]} == "$start_key" ]]; then
      sidx=$i
      break
    fi
    ((i++))
  done
  if (( sidx == 0 )); then
    ISSUES+=("no block $beid")
    continue
  fi
  # next event_id after sidx+5
  nidx=0
  i=$((sidx + sklen))
  while (( i <= blen - 10 )); do
    if [[ ${batch[$i,$((i+10))]} == '"event_id"' ]]; then
      nidx=$i
      break
    fi
    ((i++))
  done
  if (( nidx )); then
    block=${batch[$sidx,$((nidx-1))]}
  else
    block=${batch[$sidx,blen]}
  fi

  text=$OUT[$beid]

  # length_words
  lo=0; hi=0
  if [[ "$block" =~ '"length_words":[[:space:]]*\[[[:space:]]*([0-9]+)[[:space:]]*,[[:space:]]*([0-9]+)' ]]; then
    lo=$match[1]; hi=$match[2]
  fi

  # participants section
  typeset -A PARTS
  PARTS=()
  if [[ "$block" =~ '"participants":[[:space:]]*\[(.*)' ]]; then
    psec=$match[1]
    # truncate at embed
    if [[ "$psec" == *'"embed"'* ]]; then
      psec=${psec%%'"embed"'*}
    fi
    while [[ "$psec" =~ '"name":[[:space:]]*"([^"]+)"' ]]; then
      PARTS[$match[1]]=1
      psec=${psec#*\"name\":}
    done
  fi

  # embeds
  typeset -a EXPECT
  typeset -A EMB_SP EMB_ST
  EXPECT=()
  if [[ "$block" =~ '"embed":[[:space:]]*\[' ]]; then
    # from first embed to length_words
    esec=$block
    esec=${esec#*\"embed\":}
    if [[ "$esec" == *'"length_words"'* ]]; then
      esec=${esec%%'"length_words"'*}
    fi
    while [[ "$esec" =~ '"fact_id":[[:space:]]*"((F-[0-9]{4}))"' ]]; then
      fid=$match[1]
      EXPECT+=($fid)
      # slice after this fact_id
      after=${esec#*\"fact_id\":}
      after=${after#*\"$fid\"}
      st=""; sp=""
      if [[ "$after" =~ '"statement":[[:space:]]*"((\\.|[^"\\])*)"' ]]; then
        rawst=$match[1]
        # unescape
        st=""; k=1; rlen=${#rawst}
        while (( k <= rlen )); do
          ch=${rawst[$k]}
          if [[ $ch == '\' && k < rlen ]]; then
            nxt=${rawst[$((k+1))]}
            case $nxt in
              n) st+=$'\n' ;;
              \") st+='"' ;;
              \\) st+='\\' ;;
              *) st+="$nxt" ;;
            esac
            ((k+=2))
          else
            st+="$ch"; ((k++))
          fi
        done
      fi
      if [[ "$after" =~ '"speaker":[[:space:]]*"([^"]+)"' ]]; then
        sp=$match[1]
      fi
      EMB_ST[$fid]=$st
      EMB_SP[$fid]=$sp
      esec=${esec#*\"fact_id\":}
      esec=${esec#*\"$fid\"}
    done
  fi

  # cleaned text for wc
  cleaned=$text
  # strip markers keep inner — loop
  while [[ "$cleaned" =~ (⟦F-[0-9]{4}⟧)([^⟦]*)(⟦/F-[0-9]{4}⟧) ]]; do
    cleaned=${cleaned/${match[1]}${match[2]}${match[3]}/${match[2]}}
  done
  # word count
  typeset -a W
  W=(${=cleaned})
  wc=${#W}
  if (( wc < lo || wc > hi )); then
    ISSUES+=("$beid: wc=$wc not in [$lo,$hi]")
  fi

  # find markers in text with positions
  typeset -a FOUND
  typeset -A FINNER FPOS
  FOUND=()
  twork=$text
  abs_base=0
  text_copy=$text
  # iterate with match on remaining suffix; track abs index
  offset=0
  while [[ "${text_copy[$((offset+1)),-1]}" =~ '⟦((F-[0-9]{4}))⟧([^⟦]*)⟦/\1⟧' ]]; do
    fid=${match[1]}
    inner=${match[2]}
    FOUND+=($fid)
    FINNER[$fid]=$inner
    # find absolute position of ⟦fid⟧ after offset
    marker="⟦${fid}⟧"
    suffix=${text[$((offset+1)),-1]}
    # linear search for marker in suffix
    mlen=${#marker}
    slen=${#suffix}
    loc=0
    si=1
    while (( si <= slen - mlen + 1 )); do
      if [[ ${suffix[$si,$((si+mlen-1))]} == "$marker" ]]; then
        loc=$si
        break
      fi
      ((si++))
    done
    abs=$(( offset + loc - 1 ))
    # zsh strings are 1-indexed; JS m.index is 0-indexed
    # store 0-based for JS parity when doing lastIndexOf
    FPOS[$fid]=$(( abs - 1 ))
    offset=$(( abs + mlen + ${#inner} + ${#fid} + 3 ))  # ⟦/FID⟧ = 3+len(fid)+1?  ⟦ / F-0000 ⟧
    # ⟦/F-0016⟧ length = 2 + 1 + 6 + 1 = 10 for F-0016 (len fid=6)
    # marker open + inner + close: close = ⟦/ + fid + ⟧
    close="⟦/${fid}⟧"
    offset=$(( abs + mlen + ${#inner} + ${#close} - 1 ))
    # abs is 1-based start of marker; end is abs+total-1; next offset (0-based related) 
    # next search start 1-based index after close:
    offset=$(( abs + mlen + ${#inner} + ${#close} - 1 ))
  done

  # compare markers
  # JSON.stringify style
  fs="["; es="["
  i=1; for f in $FOUND; do ((i>1)) && fs+=", "; fs+="\"$f\""; ((i++)); done; fs+="]"
  i=1; for f in $EXPECT; do ((i>1)) && es+=", "; es+="\"$f\""; ((i++)); done; es+="]"
  if [[ $fs != $es ]]; then
    ISSUES+=("$beid: markers $fs!=$es")
  fi

  # speaker lines
  nl=$'\n'
  for line in ${(f)text}; do
    if [[ "$line" == *:* ]]; then
      sp=${line%%:*}
      if (( ${+PARTS[$sp]} == 0 )); then
        ISSUES+=("$beid: speaker \"$sp\" not in participants")
      fi
    fi
  done

  lines=(${(f)text})
  if (( ${#lines} > 0 )); then
    [[ "$lines[1]" == *⟦F-* ]] && ISSUES+=("$beid: embed first line")
    [[ "$lines[-1]" == *⟦F-* ]] && ISSUES+=("$beid: embed last line")
  fi

  for fid in $FOUND; do
    inner=$FINNER[$fid]
    if [[ "$inner" == *'!'* || "$inner" == *'**'* || "$inner" == *IMPORTANT* || "$inner" == *REMINDER* || "$inner" == *'NOTE:'* ]]; then
      ISSUES+=("$beid: emph in $fid")
    fi
    # CAPS \b[A-Z]{4,}\b
    typeset -a CAPS
    CAPS=()
    # tokenize on non-letters roughly
    itmp=$inner
    # use =~ repeatedly
    work=$inner
    # Replace non-alpha with space
    work2=""
    for ((ci=1; ci<=${#work}; ci++)); do
      ch=${work[$ci]}
      if [[ $ch == [A-Za-z] ]]; then
        work2+=$ch
      else
        work2+=' '
      fi
    done
    for tok in ${=work2}; do
      if [[ $tok == [A-Z][A-Z][A-Z][A-Z]* && $tok == ${tok:u} && ${#tok} -ge 4 ]]; then
        # all caps and length >= 4 — but [A-Z]{4,} means only A-Z chars
        if [[ $tok =~ '^[A-Z]{4,}$' ]]; then
          CAPS+=($tok)
        fi
      fi
    done
    if (( ${#CAPS} )); then
      ISSUES+=("$beid: CAPS [${(j:, :)CAPS}] in $fid")
    fi

    # 0-based pos
    pos0=$FPOS[$fid]
    # ls = lastIndexOf \n before pos + 1 (0-based+1 -> 1-based for zsh?)
    # In JS: ls = text.lastIndexOf('\n', pos) + 1  (0-based indexing)
    # le = text.indexOf('\n', pos); if <0 le=len
    # sp = text.slice(ls, le).split(':')[0]
    before=${text[1,$((pos0+1))]}  # chars 1..pos0+1 includes index pos0 (0-based)
    # last newline in before
    if [[ "$before" == *$nl* ]]; then
      line_prefix=${before##*$nl}
    else
      line_prefix=$before
    fi
    after=${text[$((pos0+2)),-1]}
    if [[ "$after" == *$nl* ]]; then
      line_suffix=${after%%$nl*}
    else
      line_suffix=$after
    fi
    full_line="${line_prefix}${line_suffix}"
    # Wait: before includes char at pos0 (start of marker). line_prefix is from after last nl through pos0.
    # after starts at pos0+1 (next char). Together they form the full line. Good.
    sp=${full_line%%:*}
    want=$EMB_SP[$fid]
    if [[ "$sp" != "$want" ]]; then
      ISSUES+=("$beid: $fid by $sp want $want")
    fi
    stmt=$EMB_ST[$fid]
    if [[ "$text" == *"$stmt"* ]]; then
      ISSUES+=("$beid: verbatim $fid")
    fi
    st_clean=${stmt%.}
    typeset -a SW PW
    SW=(${=st_clean})
    pin=${inner##[[:space:]]#}
    pin=${pin%%[[:space:]]#}
    PW=(${=pin})
    sw=${#SW}; pw=${#PW}
    d=$((pw - sw))
    ad=$d; (( ad < 0 )) && ad=$((-ad))
    if (( ad > 2 )); then
      ISSUES+=("$beid: $fid paraphrase wc=$pw stmt=$sw (Δ$d)")
    fi
  done

  # embeds JSON
  ej="["
  i=1
  for f in $FOUND; do
    (( i > 1 )) && ej+=", "
    ej+="\"$f\""
    ((i++))
  done
  ej+="]"
  print -r -- "$beid: $wc words [$lo-$hi] embeds=$ej" >>$VAL
done

if (( ${#ISSUES} )); then
  print -r -- "ISSUES:" >>$VAL
  for i in $ISSUES; do
    print -r -- "  $i" >>$VAL
  done
else
  print -r -- "ALL OK" >>$VAL
fi

print -r -- "RUNTIME=zsh-pure (node blocked by auto-review)" >>$VAL
