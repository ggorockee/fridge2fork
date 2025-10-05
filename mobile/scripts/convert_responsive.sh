#!/bin/bash

# Temporary script to convert hard-coded sizes to responsive sizes
# This script performs regex-based replacements

TARGET_FILE=$1

if [ -z "$TARGET_FILE" ]; then
    echo "Usage: $0 <file_path>"
    exit 1
fi

# Create backup
cp "$TARGET_FILE" "$TARGET_FILE.backup"

# Convert fontSize values (excluding AppTheme references)
perl -i -pe 's/fontSize:\s*(\d+)(?!\.sp)/fontSize: $1.sp/g' "$TARGET_FILE"

# Convert icon sizes
perl -i -pe 's/size:\s*(\d+)(?!\.sp)/size: $1.sp/g' "$TARGET_FILE"

# Convert width values (excluding double.infinity)
perl -i -pe 's/width:\s*(\d+)(?!\.w)/width: $1.w/g' "$TARGET_FILE"

# Convert height values (excluding double.infinity)
perl -i -pe 's/height:\s*(\d+)(?!\.h)/height: $1.h/g' "$TARGET_FILE"

# Convert BorderRadius.circular
perl -i -pe 's/BorderRadius\.circular\((\d+)\)/BorderRadius.circular($1.r)/g' "$TARGET_FILE"

# Convert EdgeInsets padding/margin with numeric values
perl -i -pe 's/EdgeInsets\.symmetric\(horizontal:\s*(\d+)/EdgeInsets.symmetric(horizontal: $1.w/g' "$TARGET_FILE"
perl -i -pe 's/EdgeInsets\.symmetric\(vertical:\s*(\d+)/EdgeInsets.symmetric(vertical: $1.h/g' "$TARGET_FILE"
perl -i -pe 's/EdgeInsets\.all\((\d+)\)/EdgeInsets.all($1.w)/g' "$TARGET_FILE"

# Convert SizedBox
perl -i -pe 's/SizedBox\(width:\s*(\d+)\)/SizedBox(width: $1.w)/g' "$TARGET_FILE"
perl -i -pe 's/SizedBox\(height:\s*(\d+)\)/SizedBox(height: $1.h)/g' "$TARGET_FILE"

# Convert blurRadius in BoxShadow
perl -i -pe 's/blurRadius:\s*(\d+)(?!\.r)/blurRadius: $1.r/g' "$TARGET_FILE"

# Convert Offset
perl -i -pe 's/Offset\((\d+),\s*(\d+)\)/Offset($1.w, $2.h)/g' "$TARGET_FILE"

# Convert Border width
perl -i -pe 's/width:\s*(\d+)(?!\.w),/width: $1.w,/g' "$TARGET_FILE"

echo "Conversion completed for $TARGET_FILE"
echo "Backup saved at $TARGET_FILE.backup"
