# CTranslate2 Version Strategy

## Overview
This document defines our standardized approach to CTranslate2 versioning across the VoiceStack2 project to prevent dependency conflicts and ensure consistent behavior.

## Version Decision: ctranslate2==4.0.0

### Why 4.0.0?
- **Executable Stack Compatibility**: No executable stack permission issues on Linux containers
- **Ecosystem Stability**: Compatible with faster-whisper, whisperx, and pyannote.audio
- **Docker-Friendly**: Works reliably in containerized environments
- **Proven Stable**: Avoids the executable stack errors found in 4.4.0+

### Compatibility Matrix

| Component | Version | ctranslate2 Support |
|-----------|---------|-------------------|
| torch | 2.0.0 - 2.3.x | ✅ 4.0.0 |
| faster-whisper | >=1.0.0 | ✅ 4.0.0 |
| whisperx | >=3.1.0 | ✅ 4.0.0 |
| pyannote.audio | >=3.1.0 | ✅ 4.0.0 |

### Known Issues Avoided
- **4.4.0+**: Executable stack permission errors in Linux containers
- **4.5.0+**: Requires CUDA 12 + cuDNN 9 (breaks many Docker setups)
- **>=4.3.0**: Inconsistent behavior and compatibility issues

## Implementation

### Requirements Files
Both `worker/requirements.txt` and `CURSOR.md` specify:
```
torch>=2.0.0,<2.4.0
ctranslate2==4.0.0
```

### Enforcement
- Use **exact version pinning** (`==4.0.0`) not ranges
- Include PyTorch upper bound to prevent conflicts
- All team members must use identical versions

## Migration Strategy

### From 4.0.0 → 4.4.0
1. Update requirements.txt
2. Rebuild Docker containers
3. Test full pipeline
4. Verify no regression in model loading

### From 4.5.0+ → 4.4.0
1. May need to clear model cache
2. Verify CUDA compatibility if using GPU
3. Test all audio processing components

## Monitoring
- Track any ctranslate2-related errors in logs
- Monitor for new stable releases that maintain compatibility
- Review strategy quarterly or when major dependency updates occur

## Emergency Rollback
If issues occur with 4.4.0:
- Fallback to `ctranslate2==4.0.0`
- Document specific error patterns
- Investigate root cause before advancing versions

## Decision Log
- **2024-08-17**: Standardized on 4.4.0 after 4.0.0/4.3.0 conflicts
- **Rationale**: Industry consensus for maximum compatibility
- **Next Review**: Q1 2025 or when ecosystem stabilizes

---
**Important**: Do not upgrade ctranslate2 without team consensus and thorough testing of all dependent components.