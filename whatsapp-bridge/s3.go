package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/joho/godotenv"
)

// S3Config holds AWS S3 configuration
type S3Config struct {
	Region          string
	AccessKeyID     string
	SecretAccessKey string
	SessionToken    string
	BucketName      string
}

// getS3Config returns S3 configuration from environment variables
func getS3Config() *S3Config {
	// Load .env.local file if it exists
	if err := godotenv.Load(".env.local"); err != nil {
		// If .env.local doesn't exist, try .env
		if err := godotenv.Load(".env"); err != nil {
			// If neither exists, continue with environment variables
			fmt.Printf("No .env.local or .env file found, using environment variables\n")
		}
	}

	return &S3Config{
		Region:          getEnvOrDefault("AWS_REGION", "us-east-1"),
		AccessKeyID:     os.Getenv("AWS_ACCESS_KEY_ID"),
		SecretAccessKey: os.Getenv("AWS_SECRET_ACCESS_KEY"),
		SessionToken:    os.Getenv("AWS_SESSION_TOKEN"),
		BucketName:      getEnvOrDefault("AWS_S3_BUCKET", "whatsapp-stuff"),
	}
}

// getEnvOrDefault returns environment variable value or default if not set
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// createS3Bucket creates an S3 bucket if it doesn't exist
func createS3Bucket(s3Client *s3.S3, bucketName string) error {
	// Check if bucket already exists
	_, err := s3Client.HeadBucket(&s3.HeadBucketInput{
		Bucket: aws.String(bucketName),
	})
	if err == nil {
		// Bucket already exists
		return nil
	}

	// Create bucket
	_, err = s3Client.CreateBucket(&s3.CreateBucketInput{
		Bucket: aws.String(bucketName),
	})
	return err
}

// generateFolderPath generates a folder path based on user ID and chat ID
func generateFolderPath(userID, chatJID string) string {
	// Clean the chat JID for folder name (remove special characters)
	cleanChatJID := strings.ReplaceAll(chatJID, ":", "-")
	cleanChatJID = strings.ReplaceAll(cleanChatJID, "@", "-")
	cleanChatJID = strings.ReplaceAll(cleanChatJID, ".", "-")

	// Create folder path: userID/chatJID/
	folderPath := fmt.Sprintf("%s/%s/", userID, cleanChatJID)
	return folderPath
}

// uploadToS3 uploads a file to S3 and returns the S3 URL
func uploadToS3(filePath, userID, chatJID string) (string, error) {
	config := getS3Config()
	bucketName := config.BucketName

	// Create AWS session
	sess, err := session.NewSession(&aws.Config{
		Region:      aws.String(config.Region),
		Credentials: credentials.NewStaticCredentials(config.AccessKeyID, config.SecretAccessKey, config.SessionToken),
	})
	if err != nil {
		return "", fmt.Errorf("failed to create AWS session: %v", err)
	}

	// Create S3 client
	s3Client := s3.New(sess)

	// Create bucket if it doesn't exist
	if err := createS3Bucket(s3Client, bucketName); err != nil {
		return "", fmt.Errorf("failed to create S3 bucket: %v", err)
	}

	// Read file
	fileData, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file: %v", err)
	}

	// Get filename from path
	filename := filepath.Base(filePath)

	// Generate folder path
	folderPath := generateFolderPath(userID, chatJID)

	// Create full S3 key (folder path + filename)
	s3Key := folderPath + filename

	// Upload to S3
	_, err = s3Client.PutObject(&s3.PutObjectInput{
		Bucket: aws.String(bucketName),
		Key:    aws.String(s3Key),
		Body:   bytes.NewReader(fileData),
	})
	if err != nil {
		return "", fmt.Errorf("failed to upload to S3: %v", err)
	}

	// Generate S3 URL
	s3URL := fmt.Sprintf("https://%s.s3.%s.amazonaws.com/%s", bucketName, config.Region, s3Key)
	return s3URL, nil
}
