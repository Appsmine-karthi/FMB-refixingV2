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

func timeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx, cancel := context.WithTimeout(r.Context(), timeout)
			defer cancel()
			
			r = r.WithContext(ctx)
			
			// Create a channel to signal when the request is done
			done := make(chan bool, 1)
			
			go func() {
				next.ServeHTTP(w, r)
				done <- true
			}()
			
			select {
			case <-done:
				// Request completed successfully
			case <-ctx.Done():
				// Request timed out
				if !w.Written() {
					http.Error(w, "Request timeout", http.StatusRequestTimeout)
				}
			}
		})
	}
}

func loadEnv() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
		os.Exit(1)
	}

	Events.LoadEnv()
}

func main() {
	loadEnv()
	mux := http.NewServeMux()

	mux.HandleFunc("/extractdata", func(w http.ResponseWriter, r *http.Request) {
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
	
		id, _ := body["id"].(string)
		memberId, _ := body["memberId"].(string)
	
		dataStr := Events.Extractdata(id, memberId)
		var data map[string]interface{}
		err = json.Unmarshal([]byte(dataStr), &data)
		if err != nil {
			fmt.Println("Error in unmarshal JSON:", dataStr)
			fmt.Println("Error in unmarshal JSON:", err)
			payload := map[string]interface{}{
				"success": false, 
				"Error": "failed to unmarshal JSON",
				"message": Events.LandSurveyError ,
				}
			json.NewEncoder(w).Encode(payload)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(data)
	})

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
			http.Error(w, "Failed to marshal JSON", http.StatusInternalServerError)
			return
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
	
	// Apply middleware with timeout
	handler := corsMiddleware(loggingMiddleware(timeoutMiddleware(120*time.Second)(mux)))
	
	// Configure server with better connection handling
	server := &http.Server{
		Addr:         ":5001",
		Handler:      handler,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
		MaxHeaderBytes: 1 << 20, // 1MB
	}
	
	fmt.Println("Server started at :5001")
	fmt.Println("Configured with:")
	fmt.Println("- Read timeout: 30s")
	fmt.Println("- Write timeout: 30s") 
	fmt.Println("- Idle timeout: 60s")
	fmt.Println("- Request timeout: 120s")
	
	err := server.ListenAndServe()
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
