.PHONY: build test package clean

build:
	poetry install
	# if macOS, build swift
	if [ "$(shell uname)" = "Darwin" ]; then \
		make build-swift; \
	fi

build-swift: aw_watcher_quattrod/aw-watcher-quattrod-macos

aw_watcher_quattrod/aw-watcher-quattrod-macos: aw_watcher_quattrod/macos.swift
	swiftc $^ -o $@

test:
	aw-watcher-quattrod --help

typecheck:
	poetry run mypy aw_watcher_quattrod/ --ignore-missing-imports

package:
	pyinstaller aw-watcher-quattrod.spec --clean --noconfirm

clean:
	rm -rf build dist
	rm -rf aw_watcher_quattrod/__pycache__
	rm aw_watcher_quattrod/aw-watcher-quattrod-macos
