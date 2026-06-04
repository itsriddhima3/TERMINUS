.PHONY: route_pack clean

route_pack:
	mkdir -p /app/bin /app/output
	cargo build --release
	cp -f target/release/route_pack /app/bin/route_pack
	chmod +x /app/bin/route_pack

clean:
	cargo clean
