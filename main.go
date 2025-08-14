package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
	// "mypropertyqr-landsurvey/Algs"
	"mypropertyqr-landsurvey/Events"
	"os"
	"log"
	"github.com/joho/godotenv"
	amqp "github.com/rabbitmq/amqp091-go"
)

// RabbitMQ configuration
const (
	RABBITMQ_URL = "amqp://developers:0FOPH594q8oEG@148.113.9.180:5672"
	REQUEST_QUEUE = "ms_extradata"
	RESPONSE_QUEUE = "ms_extradata_res"
)

// RabbitMQ connection and channel
var (
	rabbitConn *amqp.Connection
	rabbitChan *amqp.Channel
)

// CORS middleware function
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		
		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}

func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header first (for proxies/load balancers)
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		// X-Forwarded-For can contain multiple IPs, take the first one
		if idx := strings.Index(xff, ","); idx != -1 {
			return strings.TrimSpace(xff[:idx])
		}
		return strings.TrimSpace(xff)
	}
	
	// Check X-Real-IP header
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return strings.TrimSpace(xri)
	}
	
	// Fall back to RemoteAddr
	if idx := strings.LastIndex(r.RemoteAddr, ":"); idx != -1 {
		return r.RemoteAddr[:idx]
	}
	return r.RemoteAddr
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		clientIP := getClientIP(r)
		timestamp := time.Now().Format("2006-01-02 15:04:05")
		
		fmt.Printf("[%s] %s %s from %s\n", timestamp, r.Method, r.URL.Path, clientIP)

		next.ServeHTTP(w, r)
	})
}
var ServerPort string
func loadEnv() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
		os.Exit(1)
	}

	ServerPort = ":"+os.Getenv("GO_SERVER_PORT")

	Events.LoadEnv()
}

// Initialize RabbitMQ connection
func initRabbitMQ() error {
	var err error
	
	// Connect to RabbitMQ
	rabbitConn, err = amqp.Dial(RABBITMQ_URL)
	if err != nil {
		return fmt.Errorf("failed to connect to RabbitMQ: %v", err)
	}
	
	// Create channel
	rabbitChan, err = rabbitConn.Channel()
	if err != nil {
		return fmt.Errorf("failed to open channel: %v", err)
	}
	
	// Declare request queue
	_, err = rabbitChan.QueueDeclare(
		REQUEST_QUEUE, // name
		true,          // durable
		false,         // delete when unused
		false,         // exclusive
		false,         // no-wait
		nil,           // arguments
	)
	if err != nil {
		return fmt.Errorf("failed to declare request queue: %v", err)
	}
	
	// Declare response queue
	_, err = rabbitChan.QueueDeclare(
		RESPONSE_QUEUE, // name
		true,           // durable
		false,          // delete when unused
		false,          // exclusive
		false,          // no-wait
		nil,            // arguments
	)
	if err != nil {
		return fmt.Errorf("failed to declare response queue: %v", err)
	}
	
	fmt.Println("RabbitMQ initialized successfully")
	return nil
}

// Process message from request queue
func processMessage(msg amqp.Delivery) {
	fmt.Printf("Processing message: %s\n", string(msg.Body))
	
	// Parse the message body
	var requestData map[string]interface{}
	err := json.Unmarshal(msg.Body, &requestData)
	if err != nil {
		fmt.Printf("Error parsing message: %v\n", err)
		// Send error response
		sendResponse(map[string]interface{}{
			"success": false,
			"error":   "Invalid JSON format",
			"message": "Failed to parse request data",
		})
		msg.Ack(false)
		return
	}
	
	// Extract data from request (similar to your existing /extractdata endpoint)
	id, _ := requestData["id"].(string)
	memberId, _ := requestData["memberId"].(string)
	
	var dataMap map[string]interface{}
	err = json.Unmarshal([]byte(requestData["data"].(string)), &dataMap)	
	district, _ := dataMap["district"].(string)
	village, _ := dataMap["village"].(string)
	taluk, _ := dataMap["taluk"].(string)
	noOfSubdivision, _ := dataMap["noOfSubdivision"].(string)
	surveyNo, _ := dataMap["survey_no"].(string)
	latitude, _ := dataMap["latitude"].(string)
	longitude, _ := dataMap["longitude"].(string)

	dataStr := Events.Extractdata(id, memberId, district, village, taluk, noOfSubdivision, surveyNo, latitude, longitude)
		
	// Create response in the desired format
	response := map[string]interface{}{
		"res":    dataStr,
		"id":      id,
		"memberId": memberId,
	}

	sendResponse(response)
	
	// Acknowledge the message
	msg.Ack(false)
	
	fmt.Printf("Message processed successfully for id: %s, memberId: %s\n", id, memberId)
}

// Send response to response queue
func sendResponse(response map[string]interface{}) {
	responseBody, err := json.Marshal(response)
	if err != nil {
		fmt.Printf("Error marshaling response: %v\n", err)
		return
	}
	
	err = rabbitChan.PublishWithContext(
		context.Background(),
		"",              // exchange
		RESPONSE_QUEUE,  // routing key
		false,           // mandatory
		false,           // immediate
		amqp.Publishing{
			ContentType: "application/json",
			Body:        responseBody,
		},
	)
	
	if err != nil {
		fmt.Printf("Error publishing response: %v\n", err)
	} else {
		fmt.Printf("Response sent to queue: %s\n", RESPONSE_QUEUE)
	}
}

// Start RabbitMQ worker
func startRabbitMQWorker() {
	// Consume messages from request queue
	msgs, err := rabbitChan.Consume(
		REQUEST_QUEUE, // queue
		"",            // consumer
		false,         // auto-ack
		false,         // exclusive
		false,         // no-local
		false,         // no-wait
		nil,           // args
	)
	if err != nil {
		fmt.Printf("Failed to register consumer: %v\n", err)
		return
	}
	
	fmt.Printf("RabbitMQ worker started. Waiting for messages on queue: %s\n", REQUEST_QUEUE)
	
	// Process messages
	for msg := range msgs {
		go processMessage(msg)
	}
}

func main() {
	loadEnv()
	
	// Initialize RabbitMQ
	fmt.Println("Initializing RabbitMQ...")
	if err := initRabbitMQ(); err != nil {
		fmt.Printf("Failed to initialize RabbitMQ: %v\n", err)
		fmt.Println("Continuing without RabbitMQ...")
	} else {
		// Start RabbitMQ worker in a separate goroutine
		go startRabbitMQWorker()
		
		// Ensure RabbitMQ connection is closed when program exits
		defer func() {
			if rabbitChan != nil {
				rabbitChan.Close()
			}
			if rabbitConn != nil {
				rabbitConn.Close()
			}
			fmt.Println("RabbitMQ connections closed")
		}()
	}
	
	mux := http.NewServeMux()

	// mux.HandleFunc("/extractdata", func(w http.ResponseWriter, r *http.Request) {
	// 	if r.Method != http.MethodPost {
	// 		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	// 		return
	// 	}
	
	// 	var body map[string]interface{}
	// 	err := json.NewDecoder(r.Body).Decode(&body)
	// 	if err != nil {
	// 		http.Error(w, "Invalid JSON", http.StatusBadRequest)
	// 		return
	// 	}
	
	// 	id, _ := body["id"].(string)
	// 	memberId, _ := body["memberId"].(string)
	
	// 	dataStr := Events.Extractdata(id, memberId)
	// 	var data map[string]interface{}
	// 	err = json.Unmarshal([]byte(dataStr), &data)
	// 	if err != nil {
	// 		fmt.Println("Error in unmarshal JSON:", dataStr)
	// 		fmt.Println("Error in unmarshal JSON:", err)
	// 		payload := map[string]interface{}{
	// 			"success": false, 
	// 			"Error": "failed to unmarshal JSON",
	// 			"message": Events.LandSurveyError ,
	// 			}
	// 		json.NewEncoder(w).Encode(payload)
	// 		return
	// 	}
	// 	w.Header().Set("Content-Type", "application/json")
	// 	json.NewEncoder(w).Encode(data)
	// })

	mux.HandleFunc("/getPDF", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var body map[string]interface{}
		err := json.NewDecoder(r.Body).Decode(&body)
		if err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		dataStr, err := json.Marshal(body)
		if err != nil {
			fmt.Println("Error marshalling data:", err)
		} 
		

		id, _ := body["id"].(string)
		memberId, _ := body["memberId"].(string)
		
		response := Events.GetPdf(id, memberId, string(dataStr))

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	})
	
	mux.HandleFunc("/getrotated_coords", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var body map[string]interface{}
		err := json.NewDecoder(r.Body).Decode(&body)
		if err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}
		bodyBytes, err := json.Marshal(body)
		if err != nil {
			http.Error(w, "Failed to marshal JSON", http.StatusInternalServerError)
			return
		}

		content := string(bodyBytes)
		response := Events.GetRotatedCoords(content)
		var data map[string]interface{}
		err = json.Unmarshal([]byte(response), &data)
		if err != nil {
			fmt.Println("Error in unmarshal JSON:", response)
			http.Error(w, "Failed to unmarshal JSON", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(data)
	})

	mux.HandleFunc("/helpvideo", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		response := map[string]interface{}{
			"link": Events.HowtoLink,
			"text": Events.HowtoText,
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	})

	mux.HandleFunc("/updatedata", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var body map[string]interface{}
		err := json.NewDecoder(r.Body).Decode(&body)
		if err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}
		bodyBytes, err := json.Marshal(body)
		if err != nil {
			http.Error(w, "Failed to marshal JSON", http.StatusInternalServerError)
			return
		}
		content := string(bodyBytes)
		
		dataStr := Events.UpdateData(content)
		var data map[string]interface{}
		err = json.Unmarshal([]byte(dataStr), &data)
		if err != nil {
			fmt.Println("Error in unmarshal JSON:", dataStr)
			http.Error(w, "Failed to unmarshal JSON", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(data)
	})

	mux.HandleFunc("/UpdateFromKml", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		bodyBytes, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "Failed to read request body", http.StatusBadRequest)
			return
		}
		content := string(bodyBytes)
		dataStr, err := Events.UpdateFromKml(content)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(dataStr))
	})

	// RabbitMQ test endpoint (for testing purposes only)
	mux.HandleFunc("/test-rabbitmq", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		
		// Check if RabbitMQ is available
		if rabbitChan == nil {
			http.Error(w, "RabbitMQ not available", http.StatusServiceUnavailable)
			return
		}
		
		var body map[string]interface{}
		err := json.NewDecoder(r.Body).Decode(&body)
		if err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}
		
		// Send test message to request queue
		bodyBytes, _ := json.Marshal(body)
		err = rabbitChan.PublishWithContext(
			context.Background(),
			"",              // exchange
			REQUEST_QUEUE,   // routing key
			false,           // mandatory
			false,           // immediate
			amqp.Publishing{
				ContentType: "application/json",
				Body:        bodyBytes,
			},
		)
		
		if err != nil {
			http.Error(w, fmt.Sprintf("Failed to send message: %v", err), http.StatusInternalServerError)
			return
		}
		
		response := map[string]interface{}{
			"success": true,
			"message": "Test message sent to RabbitMQ request queue",
			"queue":   REQUEST_QUEUE,
		}
		
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	})

	mux.Handle("/kmlGUI/", http.StripPrefix("/kmlGUI/", http.FileServer(http.Dir("kmlGUI"))))
	
	handler := corsMiddleware(loggingMiddleware(mux))
	fmt.Println("Server started at "+ServerPort)
	err := http.ListenAndServe(ServerPort, handler)
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
