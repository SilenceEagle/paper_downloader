# paper_downloader

Download Papers and Supplementary from given website, such as **NIPS**, **ICLR**

## [NIPS or NeurIPS](https://nips.cc/)

*paper_download_NIPS_IDM.py* uses the IDM to download NIPS papers, the supplemental material will be merged with the main paper into one single pdf file.

forx from [Han-Jia/NIPS2018_Download](https://github.com/Han-Jia/NIPS2018_Download) and update it.

### required 
IDM
python3
bs4 (pip install bs4)
PyPDF3 (pip install PyPDF3)
tqdm (pip install tqdm)

## [ICLR](https://iclr.cc/)

*paper_download_ICLR_IDM.py* uses the IDM to download ICLR 2017-2020 oral and poster papers.

### required
IDM
python3
selenium (pip install selenium)
slugify (pip install slugify)
tqdm (pip install tqdm)
