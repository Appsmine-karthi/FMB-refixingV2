package Events

import (
	// "fmt"
	"io"
	"os"
	"net/http"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
)


// func GetFromS3(filename string, pdfpath string) bool {

// 	S3_OBJECT_NAME := "fmb_refixing/" + filename

// 	fmt.Println("Getting from S3\n\n")
// 	fmt.Println(AWS_ACCESS_KEY, AWS_SECRET_KEY)
// 	fmt.Println("\n\n")

// 	sess, err := session.NewSession(&aws.Config{
// 		Region:      aws.String(S3_REGION),
// 		Credentials: credentials.NewStaticCredentials(AWS_ACCESS_KEY, AWS_SECRET_KEY, ""),
// 	})
// 	if err != nil {
// 		fmt.Println("Error in session.NewSession:", err)
// 		return false
// 	}

// 	downloader := s3.New(sess)

// 	file, err := os.Create(pdfpath)
// 	if err != nil {
// 		fmt.Println("Error in os.Create:", err)
// 		return false
// 	}
// 	defer file.Close()

// 	input := &s3.GetObjectInput{
// 		Bucket: aws.String(BUCKET_NAME),
// 		Key:    aws.String(S3_OBJECT_NAME),
// 	}

// 	result, err := downloader.GetObject(input)
// 	if err != nil {
// 		fmt.Println("Error in downloader.GetObject:", err)
// 		return false
// 	}
// 	defer result.Body.Close()

// 	_, err = io.Copy(file, result.Body)
// 	if err != nil {
// 		fmt.Println("Error in io.Copy:", err)
// 		return false
// 	}

// 	return true
// }

func GetFromS3(filename string, pdfpath string) bool {

	url := s3Url+ filename

	resp, err := http.Get(url)
	if err != nil {
		// fmt.Println("Error in http.Get:", err)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		// fmt.Println("Non-OK HTTP status:", resp.Status)
		return false
	}

	out, err := os.Create(pdfpath)
	if err != nil {
		// fmt.Println("Error creating file:", err)
		return false
	}
	defer out.Close()

	_, err = io.Copy(out, resp.Body)
	if err != nil {
		// fmt.Println("Error saving file:", err)
		return false
	}


	return true
}

func UploadToS3(filename string, filepath string) bool {

	S3_OBJECT_NAME := "fmb_refixing/" + filename

	sess, err := session.NewSession(&aws.Config{
		Region:      aws.String(S3_REGION),
		Credentials: credentials.NewStaticCredentials(AWS_ACCESS_KEY, AWS_SECRET_KEY, ""),
	})
	if err != nil {
		// fmt.Println("Error in session.NewSession:", err)
		return false
	}

	s3Client := s3.New(sess)

	// Check if the object exists
	headInput := &s3.HeadObjectInput{
		Bucket: aws.String(BUCKET_NAME),
		Key:    aws.String(S3_OBJECT_NAME),
	}
	_, err = s3Client.HeadObject(headInput)
	if err == nil {
		// Object exists, so delete it before uploading
		delInput := &s3.DeleteObjectInput{
			Bucket: aws.String(BUCKET_NAME),
			Key:    aws.String(S3_OBJECT_NAME),
		}
		_, delErr := s3Client.DeleteObject(delInput)
		if delErr != nil {
			// fmt.Println("Error deleting existing object:", delErr)
			return false
		}
		// Optionally, wait for deletion to propagate
		err = s3Client.WaitUntilObjectNotExists(&s3.HeadObjectInput{
			Bucket: aws.String(BUCKET_NAME),
			Key:    aws.String(S3_OBJECT_NAME),
		})
		if err != nil {
			// fmt.Println("Error waiting for object deletion:", err)
			return false
		}
	}

	file, err := os.Open(filepath)
	if err != nil {
		// fmt.Println("Error in os.Open:", err)
		return false
	}
	defer file.Close()

	putInput := &s3.PutObjectInput{
		Bucket: aws.String(BUCKET_NAME),
		Key:    aws.String(S3_OBJECT_NAME),
		Body:   file,
	}

	_, err = s3Client.PutObject(putInput)
	if err != nil {
		// fmt.Println("Error in uploader.PutObject:", err)
		return false
	}

	return true
}


func SeeFromS3(filename string) bool {
	url := s3Url + filename

	resp, err := http.Get(url)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK
}
