package main

import (
	"mypropertyqr-landsurvey/Events"
)

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/extractdata", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		fmt.Fprintln(w, "extractdata")
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

	fmt.Println("Server started at :8080")
	http.ListenAndServe(":8080", nil)
}
