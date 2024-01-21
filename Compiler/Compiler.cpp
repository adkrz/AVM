#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string>
#include <vector>

#define BRAK -1
#define LICZBA 256
#define DIV 257
#define MOD 258
#define ID 259
#define KONIEC 260

struct tabsymelem {
	std::string leksem;
	int symleks = 0;
};


std::vector<tabsymelem> tabsym;

void error(const char* m);
int znajdz(const std::string& s);
int dodaj(const std::string& s, int symbleks);
void wyr();
void emituj(int s, int swart);
void wczytaj(int s);
void skl();
void czyn();

// =============================
// LEXER
// =============================

int nrwiersza = 1;
int lekswart = BRAK;

int lekser()
{
	int t;
	while (1)
	{
		t = getchar();
		if (t == ' ' || t == '\t');
		else if (t == '\n')
			nrwiersza++;
		else if (isdigit(t))
		{
			ungetc(t, stdin);
			scanf("%d", &lekswart);
			return LICZBA;
		}
		else if (isalpha(t))
		{
			int p, b = 0;
			std::string identifier;
			while (isalnum(t))
			{
				identifier += t;
				t = getchar();
				b = b + 1;
			}
			if (t != EOF)
				ungetc(t, stdin);
			p = znajdz(identifier);
			if (p < 0)
				p = dodaj(identifier, ID);
			lekswart = p;
			return tabsym[p].symleks;
			
		}
		else if (t == EOF)
			return KONIEC;
		else {
			lekswart = BRAK;
			return t;
		}
	}
}

// =============================
// PARSER
// =============================
int biezacy;
void parser() {
	biezacy = lekser();
	while (biezacy != KONIEC)
	{
		wyr();
		wczytaj(';');
	}
}

void wyr() {
	int s;
	skl();
	while (1)
	{
		switch (biezacy)
		{
		case '+':
		case '-':
			s = biezacy;
			wczytaj(biezacy);
			skl();
			emituj(s, BRAK);
			continue;
		default:
			return;
		}
	}
}

void skl()
{
	int s;
	czyn();
	while (1)
	{
		switch (biezacy)
		{
		case '*':
		case '/':
		case DIV:
		case MOD:
			s = biezacy;
			wczytaj(biezacy);
			czyn();
			emituj(s, BRAK);
			continue;
		default:
			return;
		}
	}
}

void czyn()
{
	switch (biezacy)
	{
	case '(':
		wczytaj('(');
		wyr();
		wczytaj(')');
		break;
	case LICZBA:
		emituj(LICZBA, lekswart);
		wczytaj(LICZBA);
		break;
	case ID:
		emituj(ID, lekswart);
		wczytaj(ID);
		break;
	default:
		error("Blad skladni");
	}
}

void wczytaj(int s)
{
	if (biezacy == s)
		biezacy = lekser();
	else error("Blad skladni");
}

// =============================
// EMITER
// =============================

void emituj(int s, int swart)
{
	switch (s)
	{
	case '+':
	case '-':
	case '*':
	case '/':
		printf("%c\n", s);
		break;
	case DIV:
		printf("DIV\n");
		break;
	case MOD:
		printf("MOD\n");
		break;
	case LICZBA:
		printf("%d\n", swart);
		break;
	case ID:
		printf("%s\n", tabsym[swart].leksem.c_str());
		break;
	default:
		printf("leksem %d, wartosc %d\n", s, swart);
	}
}

// =============================
// SYMBOL
// =============================

int znajdz(const std::string& s)
{
	for (int p = 0; p < tabsym.size(); p++)
		if (tabsym[p].leksem == s)
			return p;
	return -1;
}

int dodaj(const std::string& s, int symbleks)
{
	auto tmp = tabsymelem();
	tmp.leksem = s;
	tmp.symleks = symbleks;
	tabsym.push_back(tmp);
	return (int)(tabsym.size() - 1);
}

// =============================
// INIT
// =============================


void init()
{
	dodaj("div", DIV);
	dodaj("mod", MOD);
}

void error(const char* m)
{
	fprintf(stderr, "linia %d: %s\n", nrwiersza, m);
	exit(1);
}

int main()
{
	init();
	parser();
	return 0;
}