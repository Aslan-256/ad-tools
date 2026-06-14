FROM timescale/timescaledb:latest-pg15

RUN apk add --no-cache build-base make clang llvm git && \
	if ! command -v clang-19 >/dev/null 2>&1; then ln -sf "$(command -v clang)" /usr/bin/clang-19; fi && \
	if ! command -v llvm-config-19 >/dev/null 2>&1 && command -v llvm-config >/dev/null 2>&1; then ln -sf "$(command -v llvm-config)" /usr/bin/llvm-config-19; fi && \
	mkdir -p /usr/lib/llvm19/bin && \
	if [ ! -x /usr/lib/llvm19/bin/llvm-lto ] && command -v llvm-lto >/dev/null 2>&1; then ln -sf "$(command -v llvm-lto)" /usr/lib/llvm19/bin/llvm-lto; fi
COPY tulip /tulip
RUN cd /tulip && make USE_PGXS=1 install && cd / && \
	git clone https://github.com/ossc-db/pg_hint_plan --branch PG15 && \
	cd pg_hint_plan && make USE_PGXS=1 install
