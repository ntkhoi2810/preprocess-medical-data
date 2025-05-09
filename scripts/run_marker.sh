# #!/usr/bin/env bash
# #
# # run_marker.sh — script đơn giản để chạy marker với các option chuẩn
# #
# # Usage: run_marker.sh [extra-options]
# #

# # Thư mục cố định
# SOURCE_DIR=/teamspace/studios/this_studio/preprocess-medical-data/data/pdf

# # Các tuỳ chọn mặc định
# DEFAULT_OPTS=(
#   --workers 8
#   --output_dir /teamspace/studios/this_studio/preprocess-medical-data/data/markdown
#   --output_format markdown
#   --disable_image_extraction
#   --languages "vi,en"
#   # … thêm nếu cần
# )

# # Nếu bạn truyền thêm options lúc chạy script, chúng sẽ được thêm sau
# ALL_OPTS=("${DEFAULT_OPTS[@]}" "$@")

# Gọi lệnh
marker /teamspace/studios/this_studio/preprocess-medical-data/data/pdf \
  --workers 8 \
  --output_dir /teamspace/studios/this_studio/preprocess-medical-data/data/markdown \
  --output_format markdown \
  --disable_image_extraction \
  --languages "vi,en" \
