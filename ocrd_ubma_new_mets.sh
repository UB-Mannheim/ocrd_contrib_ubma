#!/bin/bash

set -x
set -e

export LANG=C.UTF-8

date --iso-8601=seconds

source /usr/local/ocrd_all/venv/bin/activate

ocrd workspace init .

for i in MAX/*.jpg; do base=`basename ${i} .jpg`; ocrd workspace add -G MAX -i MAX_${base} -g P_${base} -m image/jpeg ${i}; done

(time -p ocrd process \
  "olena-binarize -I MAX -O OCR-D-BIN -P impl sauvola" \
  "anybaseocr-crop -I OCR-D-BIN -O OCR-D-CROP" \
  "olena-binarize -I OCR-D-CROP -O OCR-D-BIN2 -P impl kim" \
  "cis-ocropy-denoise -I OCR-D-BIN2 -O OCR-D-BIN-DENOISE -P level-of-operation page" \
  "tesserocr-deskew -I OCR-D-BIN-DENOISE -O OCR-D-BIN-DENOISE-DESKEW -P operation_level page" \
  "tesserocr-segment-region -I OCR-D-BIN-DENOISE-DESKEW -O OCR-D-SEG-REG" \
  "segment-repair -I OCR-D-SEG-REG -O OCR-D-SEG-REPAIR -P plausibilize true" \
  "cis-ocropy-deskew -I OCR-D-SEG-REPAIR -O OCR-D-SEG-REG-DESKEW -P level-of-operation region" \
  "cis-ocropy-clip -I OCR-D-SEG-REG-DESKEW -O OCR-D-SEG-REG-DESKEW-CLIP -P level-of-operation region" \
  "tesserocr-segment-line -I OCR-D-SEG-REG-DESKEW-CLIP -O OCR-D-SEG-LINE" \
  "tesserocr-recognize -I OCR-D-SEG-LINE -O OCR-D-OCR-TESS -P model GT4HistOCR" \
  "fileformat-transform -I OCR-D-OCR-TESS -O OCR-D-OCR-ALTO -P from-to \"page alto\"" \
  "fileformat-transform -I OCR-D-OCR-TESS -O OCR-D-OCR-TEXT -P from-to \"page text\""
) > ocrd.log 2>&1
