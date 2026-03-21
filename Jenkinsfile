pipeline {
  agent any

  environment {
    REGISTRY = "docker.io/rohanmahakalkar"
    IMAGE_NAME = "taskmanagerapp"
    TAG = "${env.BUILD_NUMBER ?: 'latest'}"
    COMPOSE_PROJECT = "taskmanagerapp"
    KUBECONFIG = "${env.WORKSPACE}/kubeconfig"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build') {
      steps {
        sh 'echo Building Docker images'
        sh 'docker build -f fastapi-learning/Dockerfile -t ${REGISTRY}/${IMAGE_NAME}:${TAG} fastapi-learning'
      }
    }

    stage('Test') {
      steps {
        sh 'echo Running pytest'
        sh 'docker run --rm -v ${PWD}/fastapi-learning:/app -w /app ${REGISTRY}/${IMAGE_NAME}:${TAG} pytest -q'
      }
    }

    stage('Push') {
      steps {
        script {
          withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
            sh 'echo Logging into Docker Hub'
            sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
            sh 'docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}'
          }
        }
      }
    }

    stage('Deploy') {
      when {
        branch 'main'
      }
      steps {
        withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG_FILE')]) {
          sh 'cp $KUBECONFIG_FILE ${KUBECONFIG}'
          sh 'kubectl --kubeconfig ${KUBECONFIG} set image deployment/taskmanagerapp-deployment taskmanagerapp=${REGISTRY}/${IMAGE_NAME}:${TAG} --record'
          sh 'kubectl --kubeconfig ${KUBECONFIG} rollout status deployment/taskmanagerapp-deployment'
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
    }
    success {
      echo 'Pipeline succeeded!'
    }
    failure {
      echo 'Pipeline failed.'
    }
  }
}
