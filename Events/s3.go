package Events

import (
	"io"
	"os"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
)

func GetFromS3(filename string, pdfpath string) bool {
	const (
		AWS_ACCESS_KEY = "AKIAQWO5JSUX25P5VDVF"
		AWS_SECRET_KEY = "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"
		S3_REGION      = "us-east-1"
		BUCKET_NAME    = "mypropertyproduction"
	)
	S3_OBJECT_NAME := "fmb_refixing/" + filename

	sess, err := session.NewSession(&aws.Config{
		Region:      aws.String(S3_REGION),
		Credentials: credentials.NewStaticCredentials(AWS_ACCESS_KEY, AWS_SECRET_KEY, ""),
	})
	if err != nil {
		return false
	}

	downloader := s3.New(sess)

	file, err := os.Create(pdfpath)
	if err != nil {
		return false
	}
	defer file.Close()

	input := &s3.GetObjectInput{
		Bucket: aws.String(BUCKET_NAME),
		Key:    aws.String(S3_OBJECT_NAME),
	}

	result, err := downloader.GetObject(input)
	if err != nil {
		return false
	}
	defer result.Body.Close()

	_, err = io.Copy(file, result.Body)
	if err != nil {
		return false
	}

	return true
}
