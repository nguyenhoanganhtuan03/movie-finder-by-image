# Tìm kiếm phim Việt Nam đa phương thức tích hợp Chatbot

## 📋 Mô tả dự án

Ứng dụng web hỗ trợ tìm kiếm phim Việt Nam thông qua nhiều phương thức khác nhau bao gồm:
- 🖼️ Tìm kiếm qua hình ảnh
- 🎵 Tìm kiếm qua âm thanh
- 🎬 Tìm kiếm qua video
- 📝 Tìm kiếm qua mô tả ngắn
- 🤖 Chatbot RAG tích hợp hỗ trợ gợi ý và tìm kiếm thông minh

Giao diện web thân thiện, dễ sử dụng với khả năng xem phim trực tuyến cơ bản.

## 🛠️ Yêu cầu hệ thống

### Phần mềm cần thiết:
- **Python 3.10+**
- **Node.js** (phiên bản mới nhất khuyến nghị)
- **npm** hoặc **yarn**

### Framework và thư viện chính:
- **Backend**: Python với FastAPI
- **Frontend**: Vue.js
- **Database**: MongoDB
- **AI/ML**: TensorFlow, Gemini 1.5 Flash API

## 📦 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/nguyenhoanganhtuan03/movie-finder-by-image.git
cd movie-finder-by-image
```

### 2. Cài đặt Backend

```bash
# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate

# Cài đặt các thư viện Python
pip install -r requirements.txt
```

### 3. Cài đặt Frontend

#### Client (Giao diện người dùng)
```bash
cd frontend/client
npm install
```

#### Admin (Giao diện quản trị)
```bash
cd frontend/admin
npm install
```

## 🚀 Hướng dẫn sử dụng

### Khởi chạy ứng dụng

1. **Khởi động Backend Server**
```bash
python backend/server.py
```

2. **Khởi động Frontend Client** (Terminal mới)
```bash
cd frontend/client
npm run dev
```

3. **Khởi động Admin Panel** (Terminal mới)
```bash
cd frontend/admin
npm run dev
```

## ✨ Tính năng chính

### 🎬 Website xem phim cơ bản
- Giao diện người dùng thân thiện
- Danh sách phim Việt Nam phong phú
- Phát video streaming mượt mà
- Đánh giá và bình luận

### 🔍 Tìm kiếm đa phương thức

#### 1. Tìm kiếm bằng hình ảnh
- Upload ảnh poster, ảnh cảnh phim
- AI nhận diện và so khớp với database
- Kết quả chính xác cao

#### 2. Tìm kiếm bằng video
- Upload video clip ngắn
- Phân tích nội dung và so sánh
- Tìm phim từ đoạn video

#### 3. Tìm kiếm bằng âm thanh
- Upload file âm thanh/nhạc phim
- Nhận diện soundtrack, dialogue
- Matching với database âm thanh

#### 4. Tìm kiếm bằng mô tả ngắn
- Mô tả cốt truyện, nhân vật
- Natural Language Processing
- Gợi ý phim phù hợp

### 🤖 Chatbot RAG (Retrieval-Augmented Generation)
- Hỗ trợ tìm kiếm thông minh
- Gợi ý phim theo sở thích
- Trả lời câu hỏi về phim Việt Nam
- Tích hợp tất cả phương thức tìm kiếm

## 📁 Cấu trúc dự án

```
movie-finder-by-image/
├── backend/
│   ├── server.py              # Main server file
│   └── app/                   # Application code
│       ├── main.py            # Entry point for the app
│       ├── database.py        # Database configuration & connection
│       ├── models/            # AI/ML models
│       ├── controllers/       # Business logic / services
│       ├── entities/          # Database entities / ORM models
│       └── routes/            # API routes
│
├── frontend/
│   ├── client/                # User interface (Vue.js)
│   │   ├── src/
│   │   ├── public/
│   │   └── package.json
│   └── admin/                 # Admin panel (Vue.js)
│       ├── src/
│       ├── public/
│       └── package.json
│
├── data/                      # Movie database
├── models/                    # Trained AI models
├── requirements.txt           # Python dependencies
└── README.md
```

## 📞 Liên hệ

**Tác giả**: Nguyễn Hoàng Anh Tuấn
- 📱 **Điện thoại**: 0353737550
- 📧 **Email**: [nhatuan20032508@gmail.com](mailto:nhatuan20032508@gmail.com)
- 💼 **GitHub**: [@tuannguyen](https://github.com/nguyenhoanganhtuan03)

## 🙏 Lời cảm ơn

- Cảm ơn cộng đồng phát triển Vue.js và Python
- Cảm ơn các nguồn dữ liệu phim Việt Nam

---

⭐ **Nếu dự án hữu ích, hãy cho chúng tôi một star trên GitHub!**
