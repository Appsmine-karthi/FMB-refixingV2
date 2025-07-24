package main

import (
	// "encoding/json"
	// "fmt"
	"mypropertyqr-landsurvey/Algs"
	"mypropertyqr-landsurvey/Events"
)


func main() {
	Algs.InitPy()

	Events.Extractdata("4.pdf","1234567890")
}