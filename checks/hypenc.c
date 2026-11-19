/* hypenc.c: encoder B and colouring checker B for 3-uniform cases, written apart from tools/hyp.py.
   Build: cc -O2 -o hypenc hypenc.c
   hypenc enc N PATS OUT.cnf SB COLSWAP [nonstar] [hall=R1,R2,..]   writes the CNF of the scheme in tools/hyp.py's docstring (same variable
        numbering, same clause order) from its own code; compare the two files from the 'p cnf' line on.
   hypenc check COLFILE PATS               COLFILE: "n k" then one line "a b c col" per triple (any order, each
        triple once). PASS when no colour c holds a copy of pattern c (embedding search over vertex maps).
   Patterns: C3L (abx, bcy, caz), P3L (012, 234, 456), K4, K4-t (012, 013, 023), K5. PATS separated by '/'. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 40
typedef struct { int h, m; int e[16][3]; char name[16]; } HP;

static int mkpat(const char *s, HP *p) {
  memset(p, 0, sizeof *p); strncpy(p->name, s, 15);
  if (!strcmp(s, "C3L")) { int E[3][3] = {{0,1,3},{1,2,4},{2,0,5}}; p->h = 6; p->m = 3; memcpy(p->e, E, sizeof E); }
  else if (!strcmp(s, "P3L")) { int E[3][3] = {{0,1,2},{2,3,4},{4,5,6}}; p->h = 7; p->m = 3; memcpy(p->e, E, sizeof E); }
  else if (!strcmp(s, "K4-t")) { int E[3][3] = {{0,1,2},{0,1,3},{0,2,3}}; p->h = 4; p->m = 3; memcpy(p->e, E, sizeof E); }
  else if (!strcmp(s, "K4") || !strcmp(s, "K5")) {
    p->h = s[1] - '0'; p->m = 0;
    for (int a = 0; a < p->h; a++) for (int b = a + 1; b < p->h; b++) for (int c = b + 1; c < p->h; c++) {
      p->e[p->m][0] = a; p->e[p->m][1] = b; p->e[p->m][2] = c; p->m++; }
  } else return 0;
  return 1;
}

static int N, T, TID[MAXN][MAXN][MAXN];
static int tid(int a, int b, int c) { int t; if (a > b) { t = a; a = b; b = t; } if (b > c) { t = b; b = c; c = t; } if (a > b) { t = a; a = b; b = t; } return TID[a][b][c]; }

/* ---- copies: all injective maps, edge-set keys sorted, deduplicated ---- */
typedef struct { int m; int t[16]; } Copy;
static Copy *cp; static long ncp, capcp;
static int cmpint(const void *a, const void *b) { return *(const int *)a - *(const int *)b; }
static int cmpcopy(const void *a, const void *b) {
  const Copy *x = a, *y = b;
  for (int i = 0; i < x->m && i < y->m; i++) if (x->t[i] != y->t[i]) return x->t[i] < y->t[i] ? -1 : 1;
  return x->m - y->m;
}
static int img[16], used[MAXN]; static const HP *PP;
static void rec(int i) {
  if (i == PP->h) {
    if (ncp == capcp) { capcp = capcp ? 2 * capcp : 1 << 16; cp = realloc(cp, capcp * sizeof(Copy)); }
    Copy c; c.m = PP->m;
    for (int j = 0; j < PP->m; j++) c.t[j] = tid(img[PP->e[j][0]], img[PP->e[j][1]], img[PP->e[j][2]]);
    qsort(c.t, c.m, sizeof(int), cmpint);
    cp[ncp++] = c; return;
  }
  for (int v = 0; v < N; v++) if (!used[v]) { used[v] = 1; img[i] = v; rec(i + 1); used[v] = 0; }
}
static long allcopies(const HP *p) {
  ncp = 0; PP = p; memset(used, 0, sizeof used); rec(0);
  qsort(cp, ncp, sizeof(Copy), cmpcopy);
  long w = 0;
  for (long i = 0; i < ncp; i++) if (w == 0 || cmpcopy(&cp[i], &cp[w - 1])) cp[w++] = cp[i];
  ncp = w; return w;
}

static FILE *out; static long nclauses; static int topv, V, K;
static char *body; static size_t blen, bcap;
static void put(const char *s) { size_t l = strlen(s); if (blen + l + 1 > bcap) { bcap = (bcap + l + 1) * 2; body = realloc(body, bcap); } memcpy(body + blen, s, l); blen += l; body[blen] = 0; }
static void clause(int *l, int n) { char buf[32]; for (int i = 0; i < n; i++) { snprintf(buf, sizeof buf, "%d ", l[i]); put(buf); } put("0\n"); nclauses++; }
static int var(int t, int c) { return K >= 3 ? t * K + c + 1 : t + 1; }

static void lexleader(int *s) {
  int y = 0, np = 0; int *pos = malloc((V + 1) * sizeof(int));
  for (int p = 1; p <= V; p++) if (s[p] != p) pos[np++] = p;
  for (int i = 0; i < np; i++) {
    int a = pos[i], b = s[a], L = 0, buf[4];
    if (y) buf[L++] = -y;
    buf[L] = -a; buf[L + 1] = b; clause(buf, L + 2);
    if (i == np - 1) break;
    int yn = ++topv;
    buf[L] = -a; buf[L + 1] = -b; buf[L + 2] = yn; clause(buf, L + 3);
    buf[L] = a; buf[L + 1] = b; buf[L + 2] = yn; clause(buf, L + 3);
    y = yn;
  }
  free(pos);
}

static int NONSTAR, HALL[16], NHALL, FU[3][3], NFU;
static int nextcomb(int *a, int r, int n) { /* next r-subset of [n] in lexicographic order */
  int i = r - 1; while (i >= 0 && a[i] == n - r + i) i--; if (i < 0) return 0;
  a[i]++; for (int j = i + 1; j < r; j++) a[j] = a[j - 1] + 1; return 1; }
static int do_enc(int n, char *pats, const char *fn, const char *sb, int colswap) {
  HP P[64]; K = 0;
  for (char *t = strtok(pats, "/"); t; t = strtok(NULL, "/")) if (!mkpat(t, &P[K++])) { fprintf(stderr, "bad %s\n", t); return 2; }
  N = n; T = 0;
  int (*TR)[3] = malloc(sizeof(int[3]) * n * n * n);
  for (int a = 0; a < n; a++) for (int b = a + 1; b < n; b++) for (int c = b + 1; c < n; c++) { TID[a][b][c] = T; TR[T][0] = a; TR[T][1] = b; TR[T][2] = c; T++; }
  V = K >= 3 ? T * K : T; topv = V;
  if (K >= 3) for (int t = 0; t < T; t++) {
    int buf[16]; for (int c = 0; c < K; c++) buf[c] = var(t, c); clause(buf, K);
    for (int a = 0; a < K; a++) for (int b = a + 1; b < K; b++) { int l[2] = {-var(t, a), -var(t, b)}; clause(l, 2); }
  }
  int *s = malloc((V + 1) * sizeof(int));
  if (strcmp(sb, "none")) for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) {
    if (!strcmp(sb, "adj") && j != i + 1) continue;
    for (int t = 0; t < T; t++) {
      int x[3]; for (int q = 0; q < 3; q++) { int v = TR[t][q]; x[q] = v == i ? j : (v == j ? i : v); }
      int im = tid(x[0], x[1], x[2]);
      for (int c = 0; c < (K >= 3 ? K : 1); c++) s[var(t, c)] = var(im, c);
    }
    lexleader(s);
  }
  if (colswap && K >= 3) for (int a = 0; a < K; a++) for (int b = a + 1; b < K; b++) {
    if (strcmp(P[a].name, P[b].name)) continue;
    for (int t = 0; t < T; t++) for (int c = 0; c < K; c++) { int cc = c == a ? b : (c == b ? a : c); s[var(t, c)] = var(t, cc); }
    lexleader(s);
  }
  long nbase = nclauses;
  for (int c = 0; c < K; c++) {
    long m = allcopies(&P[c]);
    for (long q = 0; q < m; q++) {
      int l[16];
      for (int j = 0; j < cp[q].m; j++) l[j] = K >= 3 ? -var(cp[q].t[j], c) : (c == 0 ? -var(cp[q].t[j], 0) : var(cp[q].t[j], 0));
      clause(l, cp[q].m);
    }
  }
  if (NONSTAR && K >= 3) for (int c = 0; c < K; c++) for (int v = 0; v < n; v++) {
    int *l = malloc(T * sizeof(int)), L = 0;
    for (int t = 0; t < T; t++) if (TR[t][0] != v && TR[t][1] != v && TR[t][2] != v) l[L++] = var(t, c);
    clause(l, L); free(l);
  }
  if (NFU) {
    int t1 = tid(FU[0][0], FU[0][1], FU[0][2]), t2 = tid(FU[1][0], FU[1][1], FU[1][2]), t3 = tid(FU[2][0], FU[2][1], FU[2][2]);
    int l[2]; l[0] = var(t1, 0); clause(l, 1);
    for (int c = 2; c < K; c++) { l[0] = -var(t2, c); clause(l, 1); }
    for (int c = 3; c < K; c++) { l[0] = -var(t3, c); clause(l, 1); }
    l[0] = -var(t2, 0); l[1] = -var(t3, 2); clause(l, 2);
  }
  if (NHALL && NHALL != K - 1) { fprintf(stderr, "hall= needs k-1 values\n"); return 2; }
  for (int i = 1; i < NHALL; i++) if (HALL[i] < HALL[i - 1]) { fprintf(stderr, "hall= values must increase\n"); return 2; }
  if (strcmp(sb, "all") && strcmp(sb, "adj") && strcmp(sb, "none")) { fprintf(stderr, "sb must be all, adj or none\n"); return 2; }
  if (n > MAXN) { fprintf(stderr, "n > MAXN\n"); return 2; }
  if (NHALL && K >= 3) for (int j = 1; j < K; j++) {
    int s_ = n - HALL[K - j - 1]; if (s_ < 1) continue;
    int S[64], J[16]; for (int i = 0; i < s_; i++) S[i] = i;
    do {
      int inS[64] = {0}; for (int i = 0; i < s_; i++) inS[S[i]] = 1;
      for (int i = 0; i < j; i++) J[i] = i;
      do {
        int *l = malloc(T * K * sizeof(int)), L = 0;
        for (int q = 0; q < j; q++) for (int t = 0; t < T; t++)
          if (!inS[TR[t][0]] && !inS[TR[t][1]] && !inS[TR[t][2]]) l[L++] = var(t, J[q]);
        clause(l, L); free(l);
      } while (nextcomb(J, j, K));
    } while (nextcomb(S, s_, n));
  }
  out = fopen(fn, "w");
  fprintf(out, "c hypenc n=%d base=%ld\n", n, nbase);
  fprintf(out, "p cnf %d %ld\n", topv, nclauses);
  fwrite(body, 1, blen, out); fclose(out);
  printf("wrote %s vars=%d clauses=%ld base=%ld\n", fn, topv, nclauses, nbase);
  return 0;
}

/* ---- checker ---- */
static int COL[MAXN][MAXN][MAXN];
static int found; static int CC;
static void rec2(int i) {
  if (found) return;
  if (i == PP->h) { found = 1; return; }
  for (int v = 0; v < N && !found; v++) {
    if (used[v]) continue;
    used[v] = 1; img[i] = v;
    int ok = 1;  /* every pattern triple whose vertices are all mapped must have colour CC */
    for (int j = 0; j < PP->m && ok; j++) {
      int a = PP->e[j][0], b = PP->e[j][1], c = PP->e[j][2];
      if (a <= i && b <= i && c <= i) { int x = img[a], y = img[b], z = img[c]; if (COL[x][y][z] != CC) ok = 0; }
    }
    if (ok) rec2(i + 1);
    used[v] = 0;
  }
}
static int do_check(const char *fn, char *pats) {
  HP P[64]; int k = 0;
  for (char *t = strtok(pats, "/"); t; t = strtok(NULL, "/")) if (!mkpat(t, &P[k++])) { fprintf(stderr, "bad %s\n", t); return 2; }
  FILE *f = fopen(fn, "r"); int n, kk; if (!f || fscanf(f, "%d %d", &n, &kk) != 2 || kk != k || n > MAXN) { printf("FAIL header\n"); return 1; }
  N = n; for (int a = 0; a < n; a++) for (int b = 0; b < n; b++) for (int c = 0; c < n; c++) COL[a][b][c] = -1;
  int a, b, c, col, cnt = 0;
  while (fscanf(f, "%d %d %d %d", &a, &b, &c, &col) == 4) {
    if (a < 0 || b < 0 || c < 0 || a >= n || b >= n || c >= n || a == b || b == c || a == c || col < 0 || col >= k) { printf("FAIL line\n"); return 1; }
    int v[3] = {a, b, c};
    for (int p = 0; p < 3; p++) for (int q = 0; q < 3; q++) for (int r = 0; r < 3; r++) if (p != q && q != r && p != r) {
      if (COL[v[p]][v[q]][v[r]] != -1) { printf("FAIL repeated triple\n"); return 1; }
    }
    for (int p = 0; p < 3; p++) for (int q = 0; q < 3; q++) for (int r = 0; r < 3; r++) if (p != q && q != r && p != r) COL[v[p]][v[q]][v[r]] = col;
    cnt++;
  }
  if (cnt != n * (n - 1) * (n - 2) / 6) { printf("FAIL %d triples, expected %d\n", cnt, n * (n - 1) * (n - 2) / 6); return 1; }
  int bad = 0;
  for (CC = 0; CC < k; CC++) {
    PP = &P[CC]; found = 0; memset(used, 0, sizeof used); rec2(0);
    if (found) { printf("FAIL colour %d contains %s:", CC, P[CC].name); for (int i = 0; i < P[CC].h; i++) printf(" %d", img[i]); printf("\n"); bad = 1; }
    else printf("colour %d: no %s\n", CC, P[CC].name);
  }
  printf(bad ? "FAIL\n" : "PASS n=%d\n", n);
  return bad;
}

int main(int argc, char **argv) {
  for (int a = 7; a < argc; a++) {
    if (!strcmp(argv[a], "nonstar")) NONSTAR = 1;
    if (!strncmp(argv[a], "firstuse=", 9)) { NFU = sscanf(argv[a] + 9, "%d,%d,%d/%d,%d,%d/%d,%d,%d", &FU[0][0], &FU[0][1], &FU[0][2], &FU[1][0], &FU[1][1], &FU[1][2], &FU[2][0], &FU[2][1], &FU[2][2]) == 9; }
    if (!strncmp(argv[a], "hall=", 5)) { char *p = argv[a] + 5; while (*p) { HALL[NHALL++] = atoi(p); while (*p && *p != ',') p++; if (*p) p++; } }
  }
  if (argc >= 7 && !strcmp(argv[1], "enc")) return do_enc(atoi(argv[2]), argv[3], argv[4], argv[5], atoi(argv[6]));
  if (argc >= 4 && !strcmp(argv[1], "check")) return do_check(argv[2], argv[3]);
  fprintf(stderr, "usage: hypenc enc N PATS OUT SB COLSWAP | hypenc check COLFILE PATS\n");
  return 2;
}
