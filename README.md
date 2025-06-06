# Video Content Summarization MCP Server

A Model Context Protocol (MCP) server that extracts content from multiple video platforms and generates intelligent knowledge graphs.

## Features

### 🌐 Multi-Platform Support
- **Douyin (TikTok China)** - Short video content extraction
- **Bilibili** - Video and live streaming content
- **Xiaohongshu (Little Red Book)** - Social media posts with OCR support
- **Zhihu** - Q&A platform content

### ✨ Advanced Capabilities
- **OCR Text Recognition** - Extract text from images using PaddleOCR
- **Knowledge Graph Generation** - Intelligent content structuring
- **Chinese Content Optimization** - Specialized processing for Chinese text
- **Context-Aware Extraction** - Smart content understanding and quality control

## Installation

### Prerequisites
- Python 3.8 or higher
- Anaconda (recommended for dependency management)

### Setup
1. Clone the repository:
```bash
git clone https://github.com/fakad/video-sum-mcp.git
cd video-sum-mcp
```

2. Create and activate conda environment:
```bash
conda create -n vsc python=3.8
conda activate vsc
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### For Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "video-sum-mcp": {
      "command": "python",
      "args": ["/path/to/video-sum-mcp/main.py"],
      "cwd": "/path/to/video-sum-mcp",
      "env": {
        "CONDA_DEFAULT_ENV": "vsc"
      }
    }
  }
}
```

### For Other MCP Clients

The server can be started directly:
```bash
python main.py
```

## Usage

### Basic Video Processing
```python
# Example: Process a Bilibili video
result = process_video(
    url="https://www.bilibili.com/video/BV1234567890",
    output_format="markdown"
)
```

### Supported URL Formats
- **Douyin:** `https://v.douyin.com/...` or full URLs
- **Bilibili:** `https://www.bilibili.com/video/...`
- **Xiaohongshu:** `https://www.xiaohongshu.com/discovery/item/...`
- **Zhihu:** `https://www.zhihu.com/question/...`

### Context-Enhanced Processing
For platforms with anti-crawling measures, you can provide context:
```python
result = process_video(
    url="https://...",
    context_text="Additional context information..."
)
```

## Features in Detail

### OCR Integration
- Automatic image text extraction from Xiaohongshu posts
- PaddleOCR for accurate Chinese character recognition
- Batch processing for multiple images

### Knowledge Graph Generation
- Structured content analysis
- Intelligent relationship mapping
- Quality control and validation

### Anti-Crawling Strategies
- Smart fallback mechanisms
- Context-based extraction
- User guidance for optimal results

## Development

### Project Structure
```
video-sum-mcp/
├── core/                 # Core functionality modules
│   ├── extractors/       # Platform-specific extractors
│   ├── processors/       # Content processing logic
│   ├── knowledge_graph/  # Knowledge graph generation
│   └── managers/         # Resource management
├── scripts/              # MCP server implementation
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
└── pyproject.toml       # Project configuration
```

### Running Tests
```bash
python -m pytest
```

## Dependencies

Key dependencies include:
- `bilibili-api-python` - Bilibili API integration
- `yt-dlp` - Video downloading capabilities
- `PaddleOCR` - OCR text recognition
- `beautifulsoup4` - Web scraping
- `requests` - HTTP requests

See `requirements.txt` for complete list.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built using the [Model Context Protocol](https://modelcontextprotocol.io/)
- OCR powered by [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- Platform integrations using various open-source APIs