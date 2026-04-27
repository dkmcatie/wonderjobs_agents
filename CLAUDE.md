# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WonderJobs** is a multi-agent AI interview evaluation system with three core components:

1. **Reviewer** (✅ Complete) - Evaluates interview videos across multiple dimensions
2. **Examiner** (🔄 In Development) - Auto-generates interview questions based on job descriptions
3. **Interviewer** (📋 Planned) - AI interviewer conducts live interviews

The system analyzes candidates on three key dimensions:
- **Non-verbal**: Voice tone, facial expressions, body language
- **Content**: Answer relevance, depth, structure, job fit
- **Overall**: Comprehensive evaluation and hiring recommendation

## Architecture & Key Patterns

### API Integration Pattern
- **Provider**: Aliyun Qwen Omni API (`qwen-omni-mini` model)
- **API Base**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Key File**: `reviewer/reviewer.py` (lines 44-46)
- **Auth**: Uses `API_KEY` from environment (⚠️ Currently hardcoded in code - should be moved to env var)

### Prompt Management
- All prompts are externalized to YAML files (e.g., `reviewer/prompts.yaml`)
- Pattern: Load from YAML → Inject variables → Send to API
- Five prompt templates in reviewer: `voice_tone`, `facial_expression`, `final_evaluation`, `text_content`, `final_eval`
- Each prompt has `system` and `user` sections with template variables like `{jd}`, `{segment_id}`, `{time_range}`

### Video Processing Pipeline
```
Input Video + Timestamps
    ↓
FFmpeg Segmentation (extracts clips based on HHMMSS time ranges)
    ↓
Parallel Analysis:
    ├─ Voice/Tone Analysis (calls voice_tone prompt)
    └─ Facial Expression Analysis (calls facial_expression prompt)
    ↓
Content Analysis (analyzes transcript against JD)
    ↓
Final Synthesis (combines all results)
    ↓
Markdown Report Output
```

### Data Flow
1. **Input**: JD (md) → Resume (md) → Personality (md) → Video (mp4) → Timestamps (txt) → Transcript (txt)
2. **Processing**: Video segments analyzed in parallel via ThreadPoolExecutor
3. **Output**: Structured Markdown report with sections for tone, facial, content, and final recommendations

### Time Format Conventions
- Input/Output: `HHMMSS` format (e.g., `001230` = 00:12:30)
- Internal: Converted to float seconds for calculations
- Display: `HH:MM:SS` format (e.g., `00:12:30`)
- Functions: `parse_hhmmss()`, `seconds_to_hhmmss()`, `format_time_range()`

## Component Development

### Reviewer Component

**Entry Point**: `reviewer/reviewer.py`

**Command Line Interface**:
```bash
python reviewer.py \
  --jd <path>          # Job description (Markdown)
  --resume <path>      # Candidate resume (Markdown)
  --personality <path> # Interviewer style (Markdown)
  --video <path>       # Interview video (MP4)
  --timestamps <path>  # Time ranges (TXT)
  --transcript <path>  # Interview transcript (TXT)
  [--output <path>]    # Output report (Markdown, default: review_output.md)
```

**Key Functions**:
- `load_prompts()`: Load YAML prompt templates
- `parse_timestamps()`: Parse time range file (handles comments starting with `#`)
- `extract_segments()`: Use ffmpeg to cut video segments
- `analyze_tone_and_facial()`: Parallel voice/facial analysis
- `analyze_content()`: Transcript analysis against JD
- `generate_final_report()`: Synthesize all results

**Dependencies**:
- `pyyaml`: Load prompt templates
- `requests`: API calls to Aliyun
- `ffmpeg`: Video segmentation (system dependency)

**Install Dependencies**:
```bash
pip install pyyaml requests
brew install ffmpeg  # macOS
# or: sudo apt-get install ffmpeg  # Linux
```

### Examiner Component (In Development)

**Planned Inputs**: Job description (JD) + Interviewer profile (Markdown)

**Planned Tools**:
- WebSearch API: Find industry-standard interview questions
- RAG (Retrieval-Augmented Generation): Search historical question bank

**Expected Output**: Question candidates (Markdown) with difficulty/category classification

**Current Status**: Early stage - structure TBD

### Interviewer Component (Planned)

**Planned Role**: Conduct real-time interviews with candidates

**Expected Features**:
- Dynamic question selection based on candidate responses
- Real-time performance evaluation
- Video + transcript generation
- Feed into Reviewer component

## Development Workflow

### Setting Up a New Component
1. Create a new directory (e.g., `examiner/`, `interviewer/`)
2. Place main logic in `<component>.py`
3. Create `prompts.yaml` for prompt templates
4. Add component-specific `README.md` with usage examples
5. Follow the same arg parsing pattern as `reviewer.py`

### Common Development Tasks

**Test the Reviewer Component**:
```bash
cd reviewer/
python reviewer.py \
  --jd sample_jd.md \
  --resume sample_resume.md \
  --personality sample_personality.md \
  --video sample.mp4 \
  --timestamps sample_timestamps.txt \
  --transcript sample_transcript.txt \
  --output test_report.md
```

**Check FFmpeg Installation**:
```bash
which ffmpeg
ffmpeg -version
```

**Debug API Issues**:
- Verify `API_KEY` is set and valid
- Check Aliyun API status: https://dashscope.aliyuncs.com
- API errors appear in stdout/stderr from the request responses

**Modify Prompts Without Code Changes**:
- Edit `reviewer/prompts.yaml` directly
- The YAML structure must maintain `system` and `user` keys
- Template variables must match function calls (e.g., `{jd}`, `{segment_id}`)

## Configuration & Secrets

**⚠️ Security Note**: The API key is currently hardcoded in `reviewer/reviewer.py` line 45. This should be:
```python
API_KEY = os.getenv("ALIYUN_API_KEY")
```

**Setup**:
```bash
export ALIYUN_API_KEY="your-key-here"
```

## File Naming & Format Conventions

| Type | Format | Example |
|------|--------|---------|
| Job Description | Markdown | `job_description.md` |
| Resume | Markdown | `candidate_resume.md` |
| Personality/Style | Markdown | `interviewer_style.md` |
| Video | MP4 | `interview.mp4` |
| Timestamps | TXT | `timestamps.txt` (HHMMSS format) |
| Transcript | TXT | `transcript.txt` (plain text) |
| Output Report | Markdown | `review_output.md` |
| Prompts | YAML | `prompts.yaml` |

## Testing Strategy

The project currently lacks unit tests. When adding test infrastructure:
1. Create `tests/` directory with test files matching component names
2. Use `pytest` as the test runner
3. Mock API calls to avoid rate limits
4. Test time format parsing functions thoroughly (common edge cases: `000000`, `235959`)
5. Test ffmpeg segment extraction with short test videos

## Deployment & Integration Notes

- **Current State**: Reviewer component is production-ready for local use
- **Future Integration**: Three components will be orchestrated by a central coordinator (likely another agent)
- **Report Format**: All outputs are Markdown to enable easy integration with documentation systems
- **Parallel Processing**: Uses Python's `ThreadPoolExecutor` for concurrent API calls - adjust max_workers if rate-limited

## Useful References

- Reviewer Component Details: See `reviewer/README.md`
- Main README: See `readme.md` for project overview and roadmap
- Prompt Configuration: Edit `reviewer/prompts.yaml` to customize evaluation criteria
