# Lệnh build

docker build -t khdl_20242 .

# Lệnh run mới - ánh xạ thư mục log

# Tạo một thư mục 'logs' trên máy của bạn trước khi chạy

mkdir -p emotionapp_logs

docker run -p 8000:8000 \
 -v "$(pwd)/emotionapp_logs:/app/app/logs" \
 --name khdl_container \
 khdl_20242

docker start khdl_container

# Xem toàn bộ log từ lúc container khởi động đến giờ

docker logs khdl_container

# Xem log và tiếp tục theo dõi các log mới được tạo ra (rất hữu ích!)

docker logs -f khdl_container

docker stop khdl_container
