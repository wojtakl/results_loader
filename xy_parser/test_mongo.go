package main

import (
	"context"
	"fmt"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

const mongoURI = "mongodb://localhost:27017/?connect=direct"

func main() {
	// Create MongoDB client
	client, err := mongo.NewClient(options.Client().ApplyURI(mongoURI))
	if err != nil {
		log.Fatal("Error creating MongoDB client:", err)
	}

	// Connect to MongoDB
	err = client.Connect(context.TODO())
	if err != nil {
		log.Fatal("Error connecting to MongoDB:", err)
	} else {
		fmt.Println("Successfully connected to MongoDB!")
	}

	// Don't forget to defer closing the connection
	defer func() {
		if err := client.Disconnect(context.TODO()); err != nil {
			log.Fatal("Error disconnecting from MongoDB:", err)
		}
	}()

	// Setup the router using chi
	r := chi.NewRouter()
	r.Use(middleware.Logger)

	// Define routes here
	r.Post("/upload", uploadFile)

	// Start the server
	http.ListenAndServe(":8080", r)
}

// Example handler to upload and parse a CSV file
func uploadFile(w http.ResponseWriter, r *http.Request) {
	// Parse CSV file logic here
}
