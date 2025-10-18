# PRODUCTION-GRADE ML ENVIRONMENT REPLICATION
# Ensures 100% ML library compatibility between training and deployment
FROM python:3.11.10-slim as builder

# Set environment variables for IDENTICAL reproducible builds
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONHASHSEED=42 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 \
    CFLAGS="-O2 -march=x86-64 -mtune=generic -fstack-protector-strong" \
    CXXFLAGS="-O2 -march=x86-64 -mtune=generic -fstack-protector-strong" \
    LDFLAGS="-Wl,--as-needed"

# Remove any existing Python and reinstall for consistency
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/local/*

# Download and install Python with identical flags
RUN wget https://www.python.org/ftp/python/3.11.10/Python-3.11.10.tgz \
    && tar xzf Python-3.11.10.tgz \
    && cd Python-3.11.10 \
    && ./configure \
        --prefix=/usr/local \
        --enable-shared \
        --with-system-expat \
        --with-system-ffi \
        --with-ensurepip=yes \
        --enable-optimizations \
        --with-lto \
        CFLAGS="$CFLAGS" \
        CXXFLAGS="$CXXFLAGS" \
        LDFLAGS="$LDFLAGS" \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf Python-3.11.10*

# Install NUMPY COMPTIBLE BLAS/LAPACK for reproducible computation
RUN apt-get update && apt-get install -y \
    libopenblas0-serial \
    liblapack3 \
    libgomp1 \
    libhdf5-dev \
    libffi-dev \
    && ln -s /usr/lib/x86_64-linux-gnu/libopenblas.so.0 /usr/lib/x86_64-linux-gnu/libopenblas.so \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment with consistent seed
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pip tools and ML libraries with exact versions
COPY requirements.txt .
RUN pip install --upgrade pip==23.3.1 wheel==0.42.0 && \
    pip install --no-build-isolation \
        numpy==1.24.4 \
        scipy==1.11.3 \
        scikit-learn==1.3.2 \
        pandas==1.5.3 \
        joblib==1.3.2 && \
    pip install xgboost==1.7.6 --no-deps && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Create app directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy training data first for model training
COPY crop_yield_climate_soil_data_2019_2023.csv .
COPY models/ ./models/

# Create initial environment fingerprint BEFORE model training
RUN python src/production_environment_guard.py

# Copy application code
COPY . .

# Enforce production environment compatibility (may retrain models)
RUN python src/production_environment_guard.py

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Create model retraining cache directory
RUN mkdir -p /app/model_cache && \
    chown -R app:app /app/model_cache

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "src/prediction_api.py"]
