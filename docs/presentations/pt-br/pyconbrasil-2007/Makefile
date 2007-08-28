PDFLATEX = pdflatex

.PHONY: all clean

all: apresentacao.pdf


clean:
	rm -f *~ *.aux *.dvi *.nav *.snm *.out *.log *.toc *.vrb


apresentacao.pdf: apresentacao.tex beamerthemeFreeMobility.sty
	$(PDFLATEX) apresentacao.tex && $(PDFLATEX) apresentacao.tex