# S3 File API - WhatsApp HTTP Server

This API endpoint allows you to access S3 files using AWS credentials without exposing them to the client. It supports **all file types**, not just images.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the `whatsapp-http-server` directory:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key-here
AWS_SECRET_ACCESS_KEY=your-secret-key-here
AWS_REGION=us-west-2
AWS_S3_BUCKET=whatsapp-stuff
AWS_SESSION_TOKEN=your-session-token  # Optional, for temporary credentials
```

### 3. Run the Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Get S3 File

**Endpoint:** `GET /api/s3-file?url=<S3_URL>`

**Description:** Retrieve a file from S3 and return it as a response.

**Parameters:**
- `url` (required): The S3 URL of the file to retrieve

**Example:**
```bash
curl -X GET "http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image_20250806_085458.jpg" \
  -o image.jpg
```

**Response:**
- Returns the file content directly with appropriate headers
- Content-Type: Automatically determined from file extension
- Content-Length: Size of the file in bytes
- Cache-Control: public, max-age=3600 (1 hour cache)
- Access-Control-Allow-Origin: * (CORS enabled)

### Test S3 URL

**Endpoint:** `GET /api/test-s3?url=<S3_URL>`

**Description:** Test endpoint for debugging S3 URL parsing.

**Example:**
```bash
curl "http://localhost:8000/api/test-s3?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image.jpg"
```

**Response:**
```json
{
  "original_url": "https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image.jpg",
  "bucket": "whatsapp-stuff",
  "key": "abc/19714594907-s-whatsapp-net/image.jpg",
  "content_type": "image/jpeg"
}
```

## Supported File Types

### 🖼️ Images
- **JPEG**: `.jpg`, `.jpeg` → `image/jpeg`
- **PNG**: `.png` → `image/png`
- **GIF**: `.gif` → `image/gif`
- **BMP**: `.bmp` → `image/bmp`
- **WebP**: `.webp` → `image/webp`
- **SVG**: `.svg` → `image/svg+xml`
- **ICO**: `.ico` → `image/x-icon`
- **TIFF**: `.tiff`, `.tif` → `image/tiff`

### 📄 Documents
- **PDF**: `.pdf` → `application/pdf`
- **Word**: `.doc`, `.docx` → `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Excel**: `.xls`, `.xlsx` → `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **PowerPoint**: `.ppt`, `.pptx` → `application/vnd.ms-powerpoint`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`
- **Text**: `.txt` → `text/plain`
- **RTF**: `.rtf` → `application/rtf`
- **CSV**: `.csv` → `text/csv`
- **JSON**: `.json` → `application/json`
- **XML**: `.xml` → `application/xml`
- **HTML**: `.html`, `.htm` → `text/html`
- **CSS**: `.css` → `text/css`
- **JavaScript**: `.js` → `application/javascript`

### 🎥 Videos
- **MP4**: `.mp4` → `video/mp4`
- **AVI**: `.avi` → `video/x-msvideo`
- **MOV**: `.mov` → `video/quicktime`
- **WMV**: `.wmv` → `video/x-ms-wmv`
- **FLV**: `.flv` → `video/x-flv`
- **WebM**: `.webm` → `video/webm`
- **MKV**: `.mkv` → `video/x-matroska`
- **3GP**: `.3gp` → `video/3gpp`
- **M4V**: `.m4v` → `video/x-m4v`

### 🎵 Audio
- **MP3**: `.mp3` → `audio/mpeg`
- **WAV**: `.wav` → `audio/wav`
- **OGG**: `.ogg` → `audio/ogg`
- **AAC**: `.aac` → `audio/aac`
- **FLAC**: `.flac` → `audio/flac`
- **M4A**: `.m4a` → `audio/mp4`
- **WMA**: `.wma` → `audio/x-ms-wma`

### 📦 Archives
- **ZIP**: `.zip` → `application/zip`
- **RAR**: `.rar` → `application/vnd.rar`
- **7Z**: `.7z` → `application/x-7z-compressed`
- **TAR**: `.tar` → `application/x-tar`
- **GZ**: `.gz` → `application/gzip`

### 💻 Code/Text Files
- **Python**: `.py` → `text/x-python`
- **Java**: `.java` → `text/x-java-source`
- **C++**: `.cpp`, `.cc` → `text/x-c++src`
- **C**: `.c` → `text/x-csrc`
- **PHP**: `.php` → `text/x-php`
- **Ruby**: `.rb` → `text/x-ruby`
- **Go**: `.go` → `text/x-go`
- **Rust**: `.rs` → `text/x-rust`
- **Swift**: `.swift` → `text/x-swift`
- **Kotlin**: `.kt` → `text/x-kotlin`
- **Scala**: `.scala` → `text/x-scala`
- **Shell**: `.sh` → `application/x-sh`
- **Batch**: `.bat` → `application/x-msdos-program`
- **PowerShell**: `.ps1` → `application/x-powershell`

### 📊 Data Files
- **SQL**: `.sql` → `application/sql`
- **YAML**: `.yaml`, `.yml` → `application/x-yaml`
- **TOML**: `.toml` → `application/toml`
- **INI**: `.ini` → `text/plain`
- **Config**: `.conf` → `text/plain`
- **Log**: `.log` → `text/plain`

### 🔄 Default
- **Unknown**: Any other extension → `application/octet-stream`

## Usage Examples

### Download Different File Types

```bash
# Download an image
curl -X GET "http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image.jpg" \
  -o image.jpg

# Download a PDF
curl -X GET "http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/document.pdf" \
  -o document.pdf

# Download a video
curl -X GET "http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/video.mp4" \
  -o video.mp4

# Download an audio file
curl -X GET "http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/audio.mp3" \
  -o audio.mp3

# Download a document
curl -X GET "http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/document.docx" \
  -o document.docx
```

### View in Browser

Replace with your actual S3 URLs:
- **Image**: `http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image.jpg`
- **PDF**: `http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/document.pdf`
- **Video**: `http://localhost:8000/api/s3-file?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/video.mp4`

## Error Handling

- `400 Bad Request`: If S3 URL is missing or invalid
- `500 Internal Server Error`: If AWS credentials are invalid or S3 object doesn't exist

## Benefits

1. **Secure**: AWS credentials are not exposed to clients
2. **Universal**: Supports all file types, not just images
3. **Simple**: Just pass the S3 URL as a query parameter
4. **Direct**: Returns the actual file content, not a redirect
5. **Headers**: Preserves important S3 object metadata
6. **Caching**: Includes cache headers for better performance
7. **CORS**: Enabled for browser access

## Debugging

Use the test endpoint to debug URL parsing:
```bash
curl "http://localhost:8000/api/test-s3?url=https://whatsapp-stuff.s3.us-west-2.amazonaws.com/abc/19714594907-s-whatsapp-net/image.jpg"
```

This will return JSON with the parsed bucket, key, and content type information, which can help you troubleshoot any issues with S3 URL parsing.

## Migration Notes

This S3 File API was migrated from the Go `whatsapp-bridge` project to the Python `whatsapp-http-server` project for better integration and language consistency. The functionality remains the same, but now runs on FastAPI instead of Go's HTTP server.

### Key Changes:
- **Port**: Changed from `8080` (Go) to `8000` (Python FastAPI)
- **Framework**: FastAPI instead of Go's net/http
- **Language**: Python instead of Go
- **Dependencies**: boto3 and python-dotenv instead of AWS SDK for Go 