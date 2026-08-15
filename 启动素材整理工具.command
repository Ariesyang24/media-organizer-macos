#!/bin/zsh
set -e
TOOL_DIR="${0:A:h}"
HELPER="$TOOL_DIR/metadata_helper"
SOURCE="$TOOL_DIR/metadata_helper.swift"
APP="$TOOL_DIR/Media Organizer.app"
if [[ ! -x "$HELPER" || "$SOURCE" -nt "$HELPER" ]]; then
  mkdir -p "$TOOL_DIR/.build-cache-media-organizer/clang" "$TOOL_DIR/.build-cache-media-organizer/swift"
  CLANG_MODULE_CACHE_PATH="$TOOL_DIR/.build-cache-media-organizer/clang" SWIFT_MODULECACHE_PATH="$TOOL_DIR/.build-cache-media-organizer/swift" /usr/bin/swiftc "$SOURCE" -o "$HELPER" -module-cache-path "$TOOL_DIR/.build-cache-media-organizer/clang" -framework Foundation -framework ImageIO -framework AVFoundation -framework CoreLocation
fi
if [[ ! -x "$APP/Contents/MacOS/Media Organizer" || "$TOOL_DIR/NativeApp.swift" -nt "$APP/Contents/MacOS/Media Organizer" ]]; then
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  CLANG_MODULE_CACHE_PATH="$TOOL_DIR/.build-cache-media-organizer/clang" SWIFT_MODULECACHE_PATH="$TOOL_DIR/.build-cache-media-organizer/swift" /usr/bin/swiftc -parse-as-library "$TOOL_DIR/NativeApp.swift" -o "$APP/Contents/MacOS/Media Organizer" -module-cache-path "$TOOL_DIR/.build-cache-media-organizer/clang" -framework SwiftUI -framework AppKit -framework CoreLocation -framework UniformTypeIdentifiers -framework CryptoKit
  cp "$TOOL_DIR/Info.plist" "$APP/Contents/Info.plist"
fi
/usr/bin/open "$APP"
