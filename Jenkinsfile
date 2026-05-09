pipeline {
    agent any // This allows us to use specific agents for each stage

    environment {
        BACKEND_IMAGE = "autolead-backend"
        FRONTEND_IMAGE = "autolead-frontend"
    }

    stages {
        stage('Backend Tests') {
            agent {
                docker { 
                    image 'python:3.11-slim' 
                    reuseNode true
                }
            }
            steps {
                dir('backend') {
                    echo 'Installing backend dependencies and testing...'
                    sh 'pip install --no-cache-dir -r requirements.txt'
                    // sh 'pytest' // Uncomment when you have tests
                }
            }
        }

        stage('Frontend Build & Lint') {
            agent {
                docker { 
                    image 'node:20-alpine' 
                    reuseNode true
                }
            }
            steps {
                dir('frontend') {
                    echo 'Installing frontend dependencies...'
                    sh 'npm install'
                    sh 'npm run lint'
                    echo 'Running a test build...'
                    sh 'npm run build'
                }
            }
        }

        stage('Build Production Images') {
            // This stage runs on the main agent because it needs access to the host's Docker socket
            steps {
                echo 'Building final production-ready Docker images...'
                script {
                    sh "docker build -t ${BACKEND_IMAGE}:latest ./backend"
                    sh "docker build -t ${FRONTEND_IMAGE}:latest ./frontend"
                }
            }
        }

        stage('Cleanup') {
            steps {
                echo 'Cleaning up dangling images...'
                sh 'docker image prune -f'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Autolead is ready for deployment!'
        }
        failure {
            echo 'FAILURE: The build failed. Check the logs above.'
        }
    }
}
