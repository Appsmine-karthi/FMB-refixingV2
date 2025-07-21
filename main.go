package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"mypropertyqr-landsurvey/Events"
)

func main() {
	http.HandleFunc("/extractdata", func(w http.ResponseWriter, r *http.Request) {
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
	
		w.Header().Set("Content-Type", "application/json")
		data := Events.Extractdata(id, memberId)
		json.NewEncoder(w).Encode(data)
	})

	http.HandleFunc("/get_data/", func(w http.ResponseWriter, r *http.Request) {
		// Only allow GET method
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		// Extract data_id from URL path
		// URL: /get_data/<data_id>
		path := r.URL.Path
		prefix := "/get_data/"
		if len(path) <= len(prefix) {
			http.Error(w, "Missing data_id", http.StatusBadRequest)
			return
		}
		dataID := path[len(prefix):]
		if dataID == "" {
			http.Error(w, "Missing data_id", http.StatusBadRequest)
			return
		}
		// For demonstration, just echo the data_id
		fmt.Fprintf(w, "get_data: %s", dataID)
	})

	fmt.Println("Server started at :5001")
	err := http.ListenAndServe(":5001", nil)
	if err != nil {
		fmt.Println("Server error:", err)
	}
}
