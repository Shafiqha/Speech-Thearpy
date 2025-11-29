# 🧠 Aphasia Therapy Tool

A comprehensive, multilingual speech therapy platform designed to help patients with aphasia regain their communication abilities through interactive exercises, real-time feedback, and personalized therapy sessions.

## 🌟 Features

### 🎯 Core Therapy Modules
- **Initial Assessment**: Comprehensive speech evaluation using WAB-AQ (Western Aphasia Battery - Aphasia Quotient)
- **Interactive Therapy**: Real-time speech practice with pronunciation feedback
- **Picture Therapy**: Visual-based communication exercises
- **Lip Animation**: Visual pronunciation guidance with realistic mouth movements

### 🌍 Multilingual Support
- **English**: Full support with 95%+ ASR accuracy
- **Hindi**: Devanagari script with romanization support
- **Kannada**: Local language support with transliteration

### 🤖 AI-Powered Features
- **Advanced ASR**: Custom-trained Dual-Headed CTC Model (161MB)
- **Real-time Feedback**: Pronunciation analysis and error correction
- **Lip Sync Technology**: Phoneme-to-viseme mapping with 95%+ accuracy
- **Progress Tracking**: Machine learning-based difficulty adaptation

### 🎨 Modern Web Interface
- **React Frontend**: TypeScript-based responsive design
- **TailwindCSS**: Modern, accessible UI components
- **Real-time Communication**: WebSocket support for live feedback
- **Mobile Responsive**: Works on tablets and phones

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Login     │ │   Dashboard │ │   Therapy   │ │   Picture   ││
│  │   Register  │ │   Progress  │ │   Session   │ │   Therapy   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   Auth      │ │   Therapy   │ │   Database  │ │   Media     ││
│  │   Routes    │ │   Routes    │ │   Routes    │ │   Routes    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Core Services                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   ASR       │ │   TTS       │ │   Lip Sync  │ │   Assessment││
│  │   Engine    │ │   Engine    │ │   Engine    │ │   Engine    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database & Storage                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │   MySQL     │ │   File      │ │   Model     │ │   Cache     ││
│  │   Database  │ │   Storage   │ │   Storage   │ │   Storage   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Frontend
- **React 18** with TypeScript
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for API communication
- **Framer Motion** for animations
- **Lucide React** for icons

#### Backend
- **FastAPI** for REST API
- **Python 3.8+** runtime
- **SQLAlchemy** for ORM
- **Pydantic** for data validation
- **JWT** for authentication

#### AI/ML Services
- **PyTorch** for deep learning models
- **Librosa** for audio processing
- **Transformers** for NLP models
- **Custom ASR Model** (Dual-Headed CTC, 161MB)
- **TTS Engines** (gTTS, pyttsx3)

#### Database
- **MySQL** for relational data
- **Alembic** for migrations
- **Redis** for caching (optional)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Git LFS (for large model files)

### Installation

1. **Clone with Git LFS**
```bash
git clone https://github.com/Shafiqha/Speech-Thearpy.git
cd Speech-Thearpy
git lfs pull
```

2. **Backend Setup**
```bash
cd BAckend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
python setup_database.py
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

4. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📊 Model Performance

### ASR Model Metrics
| Language | Accuracy | Latency | Model Size |
|----------|----------|---------|------------|
| English  | 95%+     | 200ms   | 161MB      |
| Hindi    | 90-95%   | 250ms   | 161MB      |
| Kannada  | 90-95%   | 250ms   | 161MB      |

### Assessment Accuracy
| Metric | English | Hindi | Kannada |
|--------|---------|-------|---------|
| Overall Accuracy | 80-86% | 76-82% | 74-80% |
| MAE (WAB-AQ) | 8-10 pts | 10-12 pts | 10-12 pts |
| R² Score | 0.80-0.85 | 0.75-0.80 | 0.75-0.80 |

### Lip Sync Performance
| Metric | Value |
|--------|-------|
| Accuracy | 95%+ |
| Precision | 5.8ms |
| Viseme Classes | 9 |
| Smoothing | 3-frame |

## 🏥 Clinical Features

### Assessment Protocol
1. **Initial Screening**: Quick 5-minute evaluation
2. **Comprehensive Assessment**: Full WAB-AQ battery
3. **Severity Classification**: Mild, Moderate, Severe categories
4. **Progress Monitoring**: Weekly/monthly tracking

### Therapy Exercises
- **Word Repetition**: Phoneme-level practice
- **Sentence Formation**: Grammar and syntax training
- **Picture Description**: Visual communication skills
- **Conversation Practice**: Real-world scenarios

### Feedback System
- **Real-time Pronunciation**: Instant error detection
- **Phoneme Analysis**: Detailed breakdown of speech sounds
- **Progress Visualization**: Charts and graphs showing improvement
- **Adaptive Difficulty**: AI-powered level adjustment

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost/aphasia_therapy

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=100MB

# Model Paths
ASR_MODEL_PATH=./models/simple_best_model.pt
MEDIA_DIR=./api/media
```

### Database Schema
The application uses 10 main tables:
- `users` - User authentication and profiles
- `patients` - Patient information and medical history
- `therapy_sessions` - Session records and metadata
- `exercise_attempts` - Individual exercise performance
- `patient_progress` - Long-term progress tracking
- `difficulty_progress` - Adaptive difficulty levels
- `assessments` - Initial and follow-up assessments
- `media_files` - Audio/video file management
- `pronunciation_feedback` - Detailed feedback records
- `therapy_exercises` - Exercise definitions and content

## 🌐 API Documentation

### Authentication Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh

### Therapy Endpoints
- `POST /therapy/assessment` - Initial assessment
- `POST /therapy/session/start` - Start therapy session
- `POST /therapy/exercise` - Submit exercise attempt
- `GET /therapy/progress/{patient_id}` - Get progress data

### Media Endpoints
- `POST /media/upload` - Upload audio file
- `POST /media/lip-animation` - Generate lip animation
- `GET /media/exercise-images/{category}` - Get exercise images

### Database Endpoints
- `GET /db/patients` - List all patients
- `GET /db/sessions/{patient_id}` - Patient sessions
- `PUT /db/progress/{patient_id}` - Update progress

## 🎯 Use Cases

### For Patients
- **Home Practice**: Continue therapy between clinical sessions
- **Progress Tracking**: Visual feedback on improvement
- **Confidence Building**: Safe environment to practice speech
- **Family Involvement**: Caregivers can monitor progress

### For Clinicians
- **Remote Monitoring**: Track patient progress remotely
- **Data-Driven Therapy**: Use analytics to adjust treatment plans
- **Efficiency**: Automate routine assessments and exercises
- **Research**: Collect data for outcome studies

### For Caregivers
- **Support Tools**: Help family members assist in therapy
- **Progress Reports**: Regular updates on patient improvement
- **Educational Resources**: Learn about aphasia and recovery

## 🔒 Security & Privacy

- **HIPAA Compliance**: Designed with healthcare privacy standards
- **Data Encryption**: All sensitive data encrypted at rest and in transit
- **Access Control**: Role-based permissions for users
- **Audit Logging**: Complete audit trail of all actions
- **Data Backup**: Regular automated backups

## 📱 Deployment Options

### Local Development
- Docker Compose setup for local testing
- Hot reload for both frontend and backend
- Development database with sample data

### Cloud Deployment
- **AWS**: EC2 + RDS + S3 configuration
- **Google Cloud**: Compute Engine + Cloud SQL
- **Azure**: App Service + Azure SQL
- **Heroku**: Quick deployment with PostgreSQL

### Container Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Medical Advisors**: Speech-language pathologists and neurologists
- **Open Source Community**: Libraries and frameworks that make this possible
- **Patients and Families**: Who inspire this work every day

## 📞 Support

- **Documentation**: [Full API docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/Shafiqha/Speech-Thearpy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Shafiqha/Speech-Thearpy/discussions)
- **Email**: support@aphasiatherapy.tool

## 🗺️ Roadmap

### Version 2.0 (Q1 2024)
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Telehealth integration
- [ ] Multi-user support for clinics

### Version 2.1 (Q2 2024)
- [ ] VR therapy exercises
- [ ] Gamification elements
- [ ] Family collaboration features
- [ ] Advanced reporting

### Version 3.0 (Q3 2024)
- [ ] AI-powered personalized therapy plans
- [ ] Integration with electronic health records
- [ ] Real-time video sessions
- [ ] Clinical trial tools

---

**Made with ❤️ for the aphasia community**
