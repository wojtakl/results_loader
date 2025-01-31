package main

import (
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"

	"github.com/globalsign/mgo"
	"github.com/globalsign/mgo/bson"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/wcharczuk/go-chart/v2"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// MongoDB connection details
const mongoURI = "mongodb://localhost:27017/?connect=direct"
const dbName = "test_results_db"
const collectionName = "test_results"

// MongoDB session
var session *mgo.Session

// Context structure
type Context struct {
	TestName    string `json:"test_name"`
	OrderNumber string `json:"order_number"`
}

// TestResult structure
type TestResult struct {
	ID         bson.ObjectId `bson:"_id,omitempty" json:"id"`
	TestType   string        `bson:"test_type" json:"test_type"`
	FileName   string        `bson:"file_name" json:"file_name"`
	XValues    []float64     `bson:"x_values" json:"x_values"`
	YValues    []float64     `bson:"y_values" json:"y_values"`
	TestPassed bool          `bson:"test_passed" json:"test_passed"`
	Context    Context       `bson:"context" json:"context"`
}

func main() {
	// Create a MongoDB client
	client, err := mongo.NewClient(options.Client().ApplyURI(mongoURI))
	if err != nil {
		log.Fatal("Failed to create MongoDB client:", err)
	}

	// Connect to MongoDB
	err = client.Connect(context.TODO())
	if err != nil {
		log.Fatal("Failed to connect to MongoDB:", err)
	} else {
		fmt.Println("Successfully connected to MongoDB!")
	}

	// Defer closing the connection
	defer func() {
		if err := client.Disconnect(context.TODO()); err != nil {
			log.Fatal("Failed to disconnect from MongoDB:", err)
		}
	}()

	// Set up router
	r := chi.NewRouter()
	r.Use(middleware.Logger)

	r.Post("/process-file", processFileHandler)
	r.Get("/process-data", processDataHandler)
	r.Get("/generate-plot", generatePlotHandler)

	fmt.Println("Server is running on http://127.0.0.1:8006")
	log.Fatal(http.ListenAndServe(":8006", r))
}

func processFileHandler(w http.ResponseWriter, r *http.Request) {
	file, _, err := r.FormFile("file")
	fmt.Println(file)
	if err != nil {
		http.Error(w, "Failed to read file", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Extract context from file name (for example, "test_name_order_number.csv")
	filename := r.FormValue("file_name")
	fmt.Println(filename)
	fileNameParts := strings.Split(filename, "_")
	if len(fileNameParts) < 2 {
		http.Error(w, "Invalid file name format", http.StatusBadRequest)
		return
	}
	context := Context{
		TestName:    "xy",
		OrderNumber: fileNameParts[1],
	}

	// Parse CSV content
	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		http.Error(w, "Failed to parse CSV", http.StatusInternalServerError)
		return
	}

	// Extract x and y values from CSV
	var xValues, yValues []float64
	for _, record := range records {
		if len(record) < 2 {
			continue
		}
		x, err := strconv.ParseFloat(record[0], 64)
		if err != nil {
			http.Error(w, "Invalid x value", http.StatusBadRequest)
			return
		}
		y, err := strconv.ParseFloat(record[1], 64)
		if err != nil {
			http.Error(w, "Invalid y value", http.StatusBadRequest)
			return
		}
		xValues = append(xValues, x)
		yValues = append(yValues, y)
	}

	// Test passed if there are more than 100 points
	testPassed := len(xValues) > 100

	// Save to MongoDB
	testResult := TestResult{
		ID:         bson.NewObjectId(),
		TestType:   "xy",
		FileName:   filename,
		XValues:    xValues,
		YValues:    yValues,
		TestPassed: testPassed,
		Context:    context,
	}

	err = session.DB(dbName).C(collectionName).Insert(testResult)
	if err != nil {
		http.Error(w, "Failed to save test result", http.StatusInternalServerError)
		return
	}

	response := map[string]interface{}{
		"status":      "success",
		"test_passed": testPassed,
		"inserted_id": testResult.ID.Hex(),
	}
	json.NewEncoder(w).Encode(response)
}

func processDataHandler(w http.ResponseWriter, r *http.Request) {
	testID := r.URL.Query().Get("test_id")
	if !bson.IsObjectIdHex(testID) {
		http.Error(w, "Invalid test ID", http.StatusBadRequest)
		return
	}

	var result TestResult
	err := session.DB(dbName).C(collectionName).FindId(bson.ObjectIdHex(testID)).One(&result)
	if err != nil {
		http.Error(w, "Test result not found", http.StatusNotFound)
		return
	}

	response := map[string]interface{}{
		"test_id":     testID,
		"test_type":   "xy",
		"x_values":    result.XValues,
		"y_values":    result.YValues,
		"test_passed": result.TestPassed,
	}
	json.NewEncoder(w).Encode(response)
}

func generatePlotHandler(w http.ResponseWriter, r *http.Request) {
	testID := r.URL.Query().Get("test_id")
	if !bson.IsObjectIdHex(testID) {
		http.Error(w, "Invalid test ID", http.StatusBadRequest)
		return
	}

	var result TestResult
	err := session.DB(dbName).C(collectionName).FindId(bson.ObjectIdHex(testID)).One(&result)
	if err != nil {
		http.Error(w, "Test result not found", http.StatusNotFound)
		return
	}

	// Create scatter plot for X-Y values
	graph := chart.Chart{
		XAxis: chart.XAxis{
			Name: "X Values",
		},
		YAxis: chart.YAxis{
			Name: "Y Values",
		},
		Series: []chart.Series{
			chart.ContinuousSeries{
				XValues: result.XValues,
				YValues: result.YValues,
			},
		},
	}

	// Respond with PNG image of the plot
	w.Header().Set("Content-Type", "image/png")
	err = graph.Render(chart.PNG, w)
	if err != nil {
		http.Error(w, "Failed to generate plot", http.StatusInternalServerError)
	}
}
