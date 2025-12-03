# 🎬 Crunchyroll Credential Checker - Web Application

A modern, responsive web-based tool for checking Crunchyroll credentials with multi-threading support. Works seamlessly on both mobile and desktop browsers.

## ✨ Features

- 🌐 **Web-Based Interface** - Access from any browser (mobile or desktop)
- ⚡ **Multi-Threading Support** - Fast concurrent credential checking
- 🔒 **Proxy Support** - Rotate through proxies for better reliability
- 📊 **Real-Time Statistics** - Live updates without page refresh
- 💾 **Export Results** - Download valid credentials
- 📱 **Responsive Design** - Beautiful UI that works on all devices
- 🎨 **Modern Dark Theme** - Eye-friendly interface

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ibrsiaika/ibrsiaika.git
cd ibrsiaika
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
   - **Desktop**: http://localhost:5000
   - **Mobile**: http://\<your-ip\>:5000

## 📖 Usage

### 1. Upload Files

**Combo File (Required)**
- Format: `email:password` (one per line)
- Example:
  ```
  user1@example.com:password123
  user2@example.com:password456
  ```

**Proxy File (Optional)**
- Format: `ip:port` or `ip:port:user:pass` (one per line)
- Example:
  ```
  192.168.1.1:8080
  10.0.0.1:3128:username:password
  ```

### 2. Configure Settings

- Set the number of threads (1-100)
- More threads = faster checking, but use with caution

### 3. Start Checking

- Click the **Start** button
- Monitor progress in real-time
- View statistics and logs

### 4. Download Results

- Click **Download Results** to get valid credentials
- Results are saved in `valid_credentials.txt`

## 🎯 Features in Detail

### Real-Time Updates
- Uses Server-Sent Events (SSE) for instant updates
- No page refresh needed
- Live statistics: total, valid, invalid, speed, elapsed time

### Credential Checking
- Validates against Crunchyroll API
- Extracts subscription information
- Random user agent rotation
- Automatic retry on failures
- Concurrent checking with ThreadPoolExecutor

### Proxy Support
- Automatic proxy rotation
- Supports HTTP proxies
- Supports authenticated proxies
- Fallback to direct connection

### Mobile-Friendly
- Responsive grid layout
- Touch-friendly buttons
- Optimized for small screens
- Works on iOS and Android

## 📁 Project Structure

```
.
├── app.py                      # Flask backend
├── templates/
│   └── index.html             # Frontend UI
├── uploads/                   # Uploaded files (auto-created)
├── valid_credentials.txt      # Results (auto-created)
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔧 Technical Details

### Backend (Flask)
- **Framework**: Flask 3.0.0
- **Real-time**: Server-Sent Events
- **Threading**: ThreadPoolExecutor
- **File Upload**: Werkzeug secure filename
- **API Integration**: Crunchyroll Beta API

### Frontend
- **Design**: Mobile-first responsive
- **Theme**: Dark mode with gradients
- **Updates**: Real-time SSE
- **Layout**: CSS Grid & Flexbox
- **Fonts**: System fonts for performance

## 🎨 UI Preview

The application features:
- Clean, modern dark theme
- Color-coded status messages (✅ green, ❌ red)
- Real-time terminal-like log display
- Responsive statistics cards
- Smooth animations and transitions

## 🔒 Security Notes

- Uploaded files are stored temporarily
- Valid credentials are saved locally
- No data is sent to external servers (except Crunchyroll API)
- Use proxies to avoid IP blocking

## ⚙️ Configuration

You can modify the following in `app.py`:

```python
# Port (default: 5000)
app.run(host='0.0.0.0', port=5000)

# Max file size (default: 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Upload directory (default: 'uploads')
app.config['UPLOAD_FOLDER'] = 'uploads'
```

## 🐛 Troubleshooting

### Application won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 5000 is available
- Try running with: `python app.py`

### Can't access from mobile
- Ensure both devices are on the same network
- Use your computer's IP address instead of localhost
- Check firewall settings

### File upload fails
- Check file format (must be .txt)
- Ensure file size is under 16MB
- Verify combo file has correct format (email:password)

## 📝 License

This project is open source and available for educational purposes.

## 👨‍💻 Developer

**DEV-** [@noneotherthanpapa](https://t.me/noneotherthanpapa)

---

Made with ❤️ by Ibrahim
