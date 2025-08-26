# AutoQuest GCC Integration Guide

## 🎉 **GCC Frontend Integration Complete!**

Your AutoQuest project now has a fully integrated web interface for GCC (Google Cloud Console) extraction. Here's how to use it:

## 🚀 **Quick Start**

### **Option 1: Web Interface (Recommended)**

1. **Start the Backend Server:**
   ```bash
   python run.py
   ```
   The server will start on `http://localhost:8000`

2. **Start the Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```
   The frontend will start on `http://localhost:5173`

3. **Access the GCC Interface:**
   - Go to `http://localhost:5173`
   - Click on "☁️ GCC Extraction" card
   - Or navigate directly to `http://localhost:5173/gcc`

### **Option 2: Command Line (Direct)**

```bash
python run_gcc.py
```

## 🖥️ **Web Interface Features**

### **Configuration Panel**
- **Input File**: `solutions.xlsx` (your source data)
- **Output File**: `solutions_processed.xlsx` (processed results)
- **Template File**: `template.xlsx` (template structure)
- **Debug Port**: `9222` (Chrome debugging port)

### **Session Information**
- **Real-time Progress**: Live progress bar and percentage
- **Session ID**: Unique identifier for each extraction
- **Processed Companies**: Current vs total companies processed
- **Current Field**: Currently processing field

### **Controls**
- **Start Extraction**: Begin the GCC extraction process
- **Stop Extraction**: Safely stop the running extraction
- **Download Results**: Download the processed Excel file

### **Live Logs**
- **Real-time Updates**: See extraction progress in real-time
- **Error Handling**: Clear error messages and status updates
- **Log Levels**: Info, Success, Warning, Error indicators

## 🔧 **Prerequisites**

### **Required Files**
Make sure you have these files in your AutoQuest directory:
- ✅ `solutions.xlsx` - Your input data file
- ✅ `template.xlsx` - Template structure file
- ✅ Chrome browser with remote debugging enabled

### **Chrome Setup**
Start Chrome with remote debugging:
```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

## 📱 **API Endpoints**

The backend provides these REST API endpoints:

- `POST /gcc/start` - Start GCC extraction
- `GET /gcc/status/{session_id}` - Get extraction status
- `POST /gcc/stop/{session_id}` - Stop extraction
- `GET /gcc/download/{filename}` - Download results

## 🎯 **How It Works**

1. **Frontend**: React-based web interface with real-time updates
2. **Backend**: FastAPI server with GCC extraction endpoints
3. **Integration**: WebSocket-like polling for live status updates
4. **File Management**: Automatic file handling and downloads

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"No authentication token found"**
   - Get a token from the Auth page first
   - Or use the command line version

2. **"Chrome not responding"**
   - Make sure Chrome is running with `--remote-debugging-port=9222`
   - Check if port 9222 is available

3. **"File not found"**
   - Ensure `solutions.xlsx` and `template.xlsx` exist
   - Check file permissions

4. **"Import errors"**
   - Run `pip install -r requirements-minimal.txt`
   - Check Python version compatibility

### **Testing**
Run the test script to verify everything works:
```bash
python test_gcc_simple.py
```

## 📊 **Status Indicators**

- 🟢 **Running**: Extraction in progress
- 🔵 **Completed**: Successfully finished
- 🔴 **Error**: Something went wrong
- 🟡 **Stopped**: Manually stopped
- ⚪ **Idle**: Ready to start

## 🎨 **UI Components**

The frontend uses:
- **React 18** with modern hooks
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Real-time polling** for status updates
- **Responsive design** for all screen sizes

## 🔐 **Security**

- **JWT Authentication**: All API calls require valid tokens
- **File Validation**: Only allowed file types can be downloaded
- **Session Management**: Each extraction has a unique session ID

## 📈 **Performance**

- **Background Processing**: Extractions run in background tasks
- **Real-time Updates**: Status polling every 2 seconds
- **Progress Estimation**: Smart progress calculation
- **Error Recovery**: Graceful error handling and recovery

## 🚀 **Next Steps**

1. **Customize**: Modify the UI components in `frontend/src/pages/GCC.jsx`
2. **Extend**: Add more configuration options
3. **Monitor**: Add more detailed logging and analytics
4. **Scale**: Deploy to production with proper hosting

## 📞 **Support**

If you encounter issues:
1. Check the logs in the web interface
2. Run `python test_gcc_simple.py` to verify core functionality
3. Check the browser console for frontend errors
4. Verify all dependencies are installed

---

**🎉 Congratulations! Your AutoQuest GCC system is now fully integrated with a beautiful web interface!**
