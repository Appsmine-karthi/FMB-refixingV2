package Events

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mypropertyqr-landsurvey/Algs"
	"net/http"
	"os"
	"strings"
	"strconv"
	"path/filepath"
)

var nithishUrl string
var a0Url string
var sreeraguUrl string
var s3Url string

var inputDir string
var outputDir string
var pdfTempDir string

var s3jsonDir string
var s3pdfDir string
var surveyUrl string

var AWS_ACCESS_KEY string
var AWS_SECRET_KEY string
var S3_REGION string
var BUCKET_NAME string

var satJsonDir string
var s3satPdfDir string

func LoadEnv() {
	log.Println("Loading environment variables...")
	
	nithishUrl = os.Getenv("NITHISH_URL")
	a0Url = os.Getenv("A0_URL")
	sreeraguUrl = os.Getenv("SREERAGU_URL")
	s3Url = os.Getenv("S3_DOMAIN") + "/fmb_refixing/"
	inputDir = os.Getenv("INPUT_TEMP")
	outputDir = os.Getenv("OUTPUT_TEMP")
	pdfTempDir = os.Getenv("PDF_TEMP")
	s3jsonDir = os.Getenv("S3_JSON_DIR")
	s3pdfDir = os.Getenv("S3_PDF_DIR")
	s3satPdfDir = os.Getenv("S3_SAT_PDF_DIR")
	surveyUrl = os.Getenv("SURVEY_PREDICT")

	AWS_ACCESS_KEY = os.Getenv("AWS_ACCESS_KEY")
	AWS_SECRET_KEY = os.Getenv("AWS_SECRET_KEY")
	S3_REGION = os.Getenv("S3_REGION")
	BUCKET_NAME = os.Getenv("BUCKET_NAME")

	log.Println("Environment variables loaded successfully")
	log.Println("\n--------------------------------")
	log.Printf("nithishUrl: %s", nithishUrl)
	log.Printf("a0Url: %s", a0Url)
	log.Printf("sreeraguUrl: %s", sreeraguUrl)
	log.Printf("s3Url: %s", s3Url)
	log.Printf("inputDir: %s", inputDir)
	log.Printf("outputDir: %s", outputDir)
	log.Printf("s3jsonDir: %s", s3jsonDir)
	log.Printf("s3pdfDir: %s", s3pdfDir)
	log.Printf("s3satPdfDir: %s", s3satPdfDir)
	log.Printf("surveyUrl: %s", surveyUrl)
	log.Println("--------------------------------\n")
}

func doPost(url string, body map[string]interface{}) (map[string]interface{}, error) {
	log.Printf("Making POST request to: %s", url)
	log.Printf("Request body: %+v", body)

	bodyBytes, err := json.Marshal(body)
	if err != nil {
		log.Printf("Error marshaling request body: %v", err)
		panic(err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		log.Printf("Error creating HTTP request: %v", err)
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error making HTTP request: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	log.Printf("Response status: %d", resp.StatusCode)

	if resp.StatusCode != http.StatusOK {
		log.Printf("Received non-200 response: %d", resp.StatusCode)
		response := map[string]interface{}{"error": resp.StatusCode, "link": url, "payload": body}
		return response, fmt.Errorf("received non-200 response: %d", resp.StatusCode)
	}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error reading response body: %v", err)
		return nil, err
	}

	var result map[string]interface{}
	err = json.Unmarshal(respBody, &result)
	if err != nil {
		log.Printf("Error unmarshaling response: %v", err)
		response := map[string]interface{}{"error": "error in unmarshalling", "link": url, "payload": body}
		return response, fmt.Errorf("received non-200 response: %d", resp.StatusCode)
	}

	log.Printf("POST request completed successfully")
	return result, nil
}

func doGet(url string) (map[string]interface{}, error) {
	log.Printf("Making GET request to: %s", url)
	
	resp, err := http.Get(url)
	if err != nil {
		log.Printf("Error making GET request: %v", err)
		return nil, err
	}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error reading GET response body: %v", err)
		return nil, err
	}

	var result map[string]interface{}
	err = json.Unmarshal(respBody, &result)
	if err != nil {
		log.Printf("Error unmarshaling GET response: %v", err)
		return nil, err
	}

	log.Printf("GET request completed successfully")
	return result, nil
}

func downloadFile(url string, path string) error {
	log.Printf("Downloading file from %s to %s", url, path)

	if _, err := os.Stat(path); err == nil {
		log.Printf("File already exists, recreating: %s", path)
		file, err := os.Create(path)
		if err != nil {
			log.Printf("Error creating file: %v", err)
			return err
		}
		defer file.Close()

		resp, err := http.Get(url)
		if err != nil {
			log.Printf("Error downloading file: %v", err)
			return err
		}
		defer resp.Body.Close()

		_, err = io.Copy(file, resp.Body)
		if err != nil {
			log.Printf("Error copying file content: %v", err)
			return err
		}
		log.Printf("File downloaded successfully: %s", path)
		return nil
	} else if os.IsNotExist(err) {
		log.Printf("File does not exist, creating new file: %s", path)
		resp, err := http.Get(url)
		if err != nil {
			log.Printf("Error downloading file: %v", err)
			return err
		}
		defer resp.Body.Close()

		file, err := os.Create(path)
		if err != nil {
			log.Printf("Error creating file: %v", err)
			return err
		}
		defer file.Close()

		_, err = io.Copy(file, resp.Body)
		if err != nil {
			log.Printf("Error copying file content: %v", err)
			return err
		}
		log.Printf("File downloaded successfully: %s", path)
		return nil
	} else {
		log.Printf("Error checking file status: %v", err)
		return err
	}
}

func getNithish(id string, memberId string) (map[string]string, error) {
	log.Printf("Getting Nithish data for id: %s, memberId: %s", id, memberId)
	
	res, err := doPost(nithishUrl,
		map[string]interface{}{"id": id, "memberId": memberId})
	if err != nil {
		log.Printf("Error getting Nithish data: %v", err)
		return nil, err
	}
	
	district := res["data"].(map[string]interface{})["district"].(map[string]interface{})["name"].(string)
	taluk := res["data"].(map[string]interface{})["taluk"].(map[string]interface{})["name"].(string)
	village := res["data"].(map[string]interface{})["village"].(map[string]interface{})["name"].(string)
	survey_no := res["data"].(map[string]interface{})["surveyNumber"].(string)
	noOfSubdivision := res["data"].(map[string]interface{})["noOfSubdivision"].(string)
	latitude := res["data"].(map[string]interface{})["latitude"].(string)
	longitude := res["data"].(map[string]interface{})["longitude"].(string)

	result := map[string]string{
		"district":        district,
		"taluk":           taluk,
		"village":         village,
		"survey_no":       survey_no,
		"noOfSubdivision": noOfSubdivision,
		"latitude":        latitude,
		"longitude":       longitude,
	}
	
	log.Printf("Nithish data retrieved successfully: %+v", result)
	return result, nil
}

func getRaja(latitude string, longitude string) (string, error) {
	log.Printf("Getting Raja data for lat: %s, lon: %s", latitude, longitude)
	
	res, err := doGet(surveyUrl+"?lat=" + latitude + "&lon=" + longitude)
	if err != nil {
		log.Printf("Error in getRaja: %v", err)
		return "", err
	}

	jsonBytes, err := json.Marshal(res)
	if err != nil {
		log.Printf("JSON marshal error in getRaja: %v", err)
		return "", err
	}
	
	log.Printf("Raja data retrieved successfully")
	return string(jsonBytes), nil
}

func getA0(payload map[string]string) (map[string]interface{}, error) {
	url := a0Url + payload["district"] + "/" + payload["taluk"] + "/" + payload["village"] + "/" + payload["survey_no"]
	log.Printf("Getting A0 data from: %s", url)
	
	res, err := doGet(url)
	if err != nil {
		log.Printf("Error in getA0: %v", err)
		return nil, err
	}

	log.Printf("A0 data retrieved successfully")
	return res, nil
}

func Extractdata(id string, memberId string) string {

	log.Printf("\n\n\n\n--------------------------------")
	log.Printf("Starting Extractdata for id: %s, memberId: %s", id, memberId)
	
	details, err := getNithish(id, memberId)
	if err != nil {
		log.Printf("Failed to get Nithish data: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Failed to Extract",
			"surveyStatusCode":  0,
			"remarks":           "Failed to get Id details",
			"surveyStatusAlert": "",
		}
		_, _ = doPost(sreeraguUrl, payload)

		resultJSON, _ := json.Marshal(payload)
		return string(resultJSON)
	}

	log.Printf("Retrieved details: %+v", details)

	noOfSubdivision, _ := strconv.Atoi(details["noOfSubdivision"])
	if noOfSubdivision > 100 {
		log.Printf("Number of subdivisions (%d) exceeds limit of 25", noOfSubdivision)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           fmt.Sprintf("noOfSubdivision null or 0 or >%d", noOfSubdivision),
			"surveyStatusAlert": MoreSurvey,
		}
		_, _ = doPost(sreeraguUrl, payload)

		resultJSON, _ := json.Marshal(payload)
		return string(resultJSON)
	}

	log.Printf("Starting concurrent Raja data retrieval")
	rajaCh := make(chan struct {
		result string
		err    error
	})
	go func() {
		result, err := getRaja(details["latitude"], details["longitude"])
		rajaCh <- struct {
			result string
			err    error
		}{result, err}
	}()

	Localfilename := strings.ReplaceAll(inputDir+details["district"]+details["taluk"]+details["village"]+details["survey_no"]+".pdf", " ", "_")
	S3filename := strings.ReplaceAll(s3pdfDir+details["district"]+details["taluk"]+details["village"]+details["survey_no"]+".pdf", " ", "_")
	
	Localjsonname := strings.ReplaceAll(outputDir+details["district"]+details["taluk"]+details["village"]+details["survey_no"]+".json", " ", "_")
	S3jsonname := strings.ReplaceAll(s3jsonDir+details["district"]+details["taluk"]+details["village"]+details["survey_no"]+".json", " ", "_")
	
	log.Printf("Local filename: %s", Localfilename)
	log.Printf("S3 filename: %s", S3filename)
	log.Printf("Local JSON name: %s", Localjsonname)
	log.Printf("S3 JSON name: %s", S3jsonname)
	
	isJsonInS3 := GetFromS3(
		S3jsonname,
		Localjsonname,
	)
	// isJsonInS3 = false
	log.Printf("JSON exists in S3: %t", isJsonInS3)
	if isJsonInS3 {
		log.Printf("Reading existing JSON from S3")
		data, err := os.ReadFile(Localjsonname)
		if err != nil {
			log.Printf("Error reading JSON file: %v", err)
		}
		if err == nil{
			log.Printf("Successfully read JSON file, removing local copy")
			os.Remove(Localjsonname)
			payload := map[string]interface{}{
				"id":                id,
				"memberId":          memberId,
				"surveyStatus":      "Ready to Survey",
				"surveyStatusCode":  2,
				"remarks":           "completed rotation",
				"surveyStatusAlert": "ready",
				"downloadDocument" : s3Url + S3filename,
			}
			_, _ = doPost(sreeraguUrl, payload)
			return string(data)
		}
	}

	isPdfInS3 := GetFromS3(
		S3filename,
		Localfilename,
	)
	log.Printf("PDF exists in S3: %t", isPdfInS3)
	
	if !isPdfInS3 {
		log.Printf("PDF not in S3, fetching from A0")
		a0, err := getA0(details)
		if err != nil {
			log.Printf("Error in getA0: %v", err)
			payload := map[string]interface{}{
				"id":                id,
				"memberId":          memberId,
				"surveyStatus":      "Failed to Extract",
				"surveyStatusCode":  0,
				"remarks":           "Failed to get A0 FMB",
				"surveyStatusAlert": "",
			}
			_, _ = doPost(sreeraguUrl, payload)
			return `{"success": false, "Error": "Failed to get A0 FMB", "message": "` + LandSurveyError + `,error: ` + err.Error() + `"}`
		}
		if a0["message"] != "File uploaded successfully" {
			log.Printf("A0 response indicates failure: %v", a0["error"])
			payload := map[string]interface{}{
				"id":                id,
				"memberId":          memberId,
				"surveyStatus":      "Failed to Extract",
				"surveyStatusCode":  0,
				"remarks":           "Failed to get A0 FMB: " + fmt.Sprintf("%v", a0["error"]),
				"surveyStatusAlert": "",
			}
			_, _ = doPost(sreeraguUrl, payload)

			return `{"success": false, "Error": "Failed to get A0 FMB", "message": Failed to get A0 FMB ,"error": ` + fmt.Sprintf("%v", a0["error"]) + `"}`
		}

		log.Printf("A0 data retrieved successfully, updating status")
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "completed pdf extraction",
			"downloadDocument" : s3Url + S3filename,
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)

		pdfUrl := a0["data"].([]any)[0].(string)
		log.Printf("Downloading PDF from: %s", pdfUrl)
		err = downloadFile(pdfUrl, Localfilename)
		if err != nil {
			log.Printf("Error in downloadFile: %v", err)
			return `{"success": false, "Error": "Failed to download file", "message": Failed to download file","error": ` + err.Error() + `"}`
		}
		
		log.Printf("Uploading PDF to S3")
		uploaded := UploadToS3(S3filename, Localfilename)
		if !uploaded {
			log.Printf("Error in UploadToS3: %s", S3filename)
			return `{"success": false, "Error": "Failed to upload file", "message": Failed to upload file","error": ` + err.Error() + `"}`
		}
		log.Printf("PDF uploaded to S3 successfully")
	}

	defer os.Remove(Localfilename)

	log.Printf("Starting PDF processing with Pycess")
	response, err := Algs.Pycess(Algs.PyParam{
		Mod: "ExtractPdf",
		Arg: []any{Localfilename},
	})
	if err != nil || response[0] == '!'{
		log.Printf("Error in ExtractPdf Pycess: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to extract pdf (pycess)",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "ExtractPdf", "message": "` + LandSurveyError + `,"error": ` + err.Error() + `"}`
	}

	log.Printf("PDF extraction completed, unmarshaling response")
	var res Algs.PyRes
	err = json.Unmarshal([]byte(response), &res)
	if err != nil || response[0] == '!'{
		log.Printf("Error unmarshaling PyRes: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to extract pdf (unmarshal)",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "ExtractPdf unmarshal", "message": "` + LandSurveyError + `,"error": ` + err.Error() + `"}`
	}

	log.Printf("Processing extracted data")
	res.Line3 = Algs.RemoveFloatingLines(res.Line3)

	res.Line1 = Algs.RemoveArrows(res.Line1)

	

	// log.Printf("\n\n\n--------------------------------")
	// fmt.Println(res.Line1)
	// log.Printf("--------------------------------\n\n\n")

	Algs.OffsetToOrigin(&res)

	seen := make(map[string]bool)
	var points []Algs.Point

	for _, seg := range res.Line3 {
		for _, p := range seg {
			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
			if !seen[key] {
				seen[key] = true
				points = append(points, Algs.Point{p[0], p[1]})
			}
		}
	}
	for _, seg := range res.Line1 {
		for _, p := range seg {
			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
			if !seen[key] {
				seen[key] = true
				points = append(points, Algs.Point{p[0], p[1]})
			}
		}
	}
	
	log.Printf("Processing coordinates and labels")
	CoordRed := Algs.RankBasedAssignment(points, res.R)
	CoordBlue := Algs.FormatBbox(res.B)

	CoordRedMap := make(map[Algs.Point]string)
	for key, value := range CoordRed {
		CoordRedMap[value] = key
	}

	for _, seg := range res.Line1_ {
		for _, p := range seg {
			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
			if !seen[key] {
				seen[key] = true
				points = append(points, Algs.Point{p[0], p[1]})
			}
		}
	}

	counter := 0
	for _, pnt := range points {
		if _, exists := CoordRedMap[pnt]; !exists {
			st := fmt.Sprintf("t%d", counter)
			CoordRedMap[pnt] = st
			CoordRed[st] = pnt
			counter++
		}
	}



	log.Printf("Getting subdivision data")
	str, err := json.Marshal([]any{CoordBlue, res.Line1, res.Line3, res.Xmax - res.Xmin, res.Ymax - res.Ymin})
	if err != nil {
		log.Printf("Error marshaling Line1 to JSON: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to get subdiv (marshal)",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "getSubdiv marshal", "message": "` + LandSurveyError + `,"error": ` + err.Error() + `"}`
	}
	
	response, err = Algs.Pycess(Algs.PyParam{
		Mod: "getSubdiv",
		Arg: []any{string(str)},
	})
	if err != nil || response[0] == '!'{
		log.Printf("Error in getSubdiv Pycess: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to get subdiv (pycess)",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "getSubdiv", "message": "` + LandSurveyError + `,"error": ` + err.Error() + `"}`
	}

	var subdivResult map[string][][][]float32
	err = json.Unmarshal([]byte(response), &subdivResult)
	if err != nil {
		log.Printf("Error unmarshaling subdiv JSON: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to get subdiv (unmarshal)",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "getSubdiv unmarshal", "message": "` + LandSurveyError + `,"error": ` + err.Error() + `"}`
	}

	log.Printf("Processing subdivision results")
	for ind := range CoordBlue {
		subdivResult[ind] = Algs.OrderLines(subdivResult[ind])
	}

	for ind := range subdivResult {
		newPol := [][][]float32{}
		for _, pol := range subdivResult[ind] {
			newLne := [][]float32{}
			for _, lne := range pol {
				_, exists := CoordRedMap[Algs.Point{lne[0], lne[1]}]
				if exists {
					newLne = append(newLne, lne)
				}
			}
			newPol = append(newPol, newLne)
		}
		subdivResult[ind] = newPol
	}

	log.Printf("Building coordinates and lines data")
	coordinates := make(map[string][]any)
	for c := range CoordRed {
		temp := CoordRed[c]
		coordinates[c] = []any{[]float32{temp.X, temp.Y}, "main", []string{"notmodified", "notmodified"}}
	}
	lines := make([]map[string]any, 0, len(res.Line3))
	for _, seg := range res.Line1_ {
		lines = append(lines, map[string]any{
			"coordinates": []string{CoordRedMap[Algs.Point{seg[0][0], seg[0][1]}], CoordRedMap[Algs.Point{seg[1][0], seg[1][1]}]},
			"length":      Algs.Distance(Algs.Point{seg[0][0], seg[0][1]}, Algs.Point{seg[1][0], seg[1][1]}),
			"dashes":      "[ 30 10 1 3 1 3 1 10 ] 1",
			"strokewidth": "1",
		})
	}
	// for _, subdivPolys := range subdivResult {
	// 	for _, poly := range subdivPolys {
	// 		for i := 0; i < len(poly)-1; i++ { 
	// 			start := poly[i]
	// 			end := poly[i+1]
	// 			lines = append(lines, map[string]any{
	// 				"coordinates": []string{
	// 					CoordRedMap[Algs.Point{start[0], start[1]}],
	// 					CoordRedMap[Algs.Point{end[0], end[1]}],
	// 				},
	// 				"length":      Algs.Distance(Algs.Point{start[0], start[1]}, Algs.Point{end[0], end[1]}),
	// 				"dashes":      "[ 9 0 ] 1",
	// 				"strokewidth": "1",
	// 			})
	// 		}
	// 	}
	// }
	for _, seg := range res.Line1 {
		lines = append(lines, map[string]any{
			"coordinates": []string{CoordRedMap[Algs.Point{seg[0][0], seg[0][1]}], CoordRedMap[Algs.Point{seg[1][0], seg[1][1]}]},
			"length":      Algs.Distance(Algs.Point{seg[0][0], seg[0][1]}, Algs.Point{seg[1][0], seg[1][1]}),
			"dashes":      "[ 9 0 ] 1",
			"strokewidth": "1",
		})
	}
	for _, seg := range res.Line3 {
		lines = append(lines, map[string]any{
			"coordinates": []string{CoordRedMap[Algs.Point{seg[0][0], seg[0][1]}], CoordRedMap[Algs.Point{seg[1][0], seg[1][1]}]},
			"length":      Algs.Distance(Algs.Point{seg[0][0], seg[0][1]}, Algs.Point{seg[1][0], seg[1][1]}),
			"dashes":      "[ 9 0 ] 1",
			"strokewidth": "3",
		})
	}

	
	subdiv_list := make(map[string]any)
	for key, subdivPolys := range subdivResult {
		flattened := Algs.FlattenPoints(subdivPolys)
		flattenedArr := []string{}
		grp := []any{}
		for _, lne := range flattened {
			temp := Algs.Point{lne[0], lne[1]}
			flattenedArr = append(flattenedArr, CoordRedMap[temp])
		}

		if len(flattenedArr) == 0 {
			continue
		}

		grp = append(grp, []any{CoordBlue[key].X, CoordBlue[key].Y})
		grp = append(grp, flattenedArr)
		grp = append(grp, Algs.CalculateArea(flattened))

		subdiv_list[key] = grp
	}

	log.Printf("Marshaling final data structure")
	data, err := json.Marshal(map[string]any{"lines": lines, "subdivision_list": subdiv_list, "coordinates": coordinates, "Scale": res.Scale, "district": details["district"], "taluk": details["taluk"], "village": details["village"], "survey_no": details["survey_no"]})
	if err != nil {
		log.Printf("Error marshaling lines: %v", err)
	}

	log.Printf("Running shrink_or_expand_points")
	response, err = Algs.Pycess(Algs.PyParam{
		Mod: "shrink_or_expand_points",
		Arg: []any{string(data)},
	})
	if err != nil || response[0] == '!'{
		log.Printf("Error in shrink_or_expand_points: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to shrink or expand points",
			"surveyStatusAlert": LandSurveyError,
			"downloadDocument" : s3Url + S3filename,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "shrink_or_expand_points", "message": "` + LandSurveyError + `,"error": ` + err.Error() + `"}`
	}

	log.Printf("Waiting for Raja data")
	rajaRes := <-rajaCh
	if rajaRes.err != nil {
		log.Printf("Error in rajaRes: %v", rajaRes.err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to get world coordinates",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "rajaRes", "message": "` + LandSurveyError + `,"error": ` + rajaRes.err.Error() + `"}`
	}
	raja := rajaRes.result
	log.Printf("Raja data received successfully")

	log.Printf("Running rotate operation")
	response, err = Algs.Pycess(Algs.PyParam{
		Mod: "rotate",
		Arg: []any{response, raja},
	})
	if err != nil || response[0] == '!'{
		log.Printf("Error in rotate: %v", err)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           "failed to rotate (pycess)",
			"surveyStatusAlert": LandSurveyError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "rotate", "message": "` + LandSurveyError + `","error": "` + err.Error() + `"}`
	}

	log.Printf("Processing completed successfully, updating final status")
	payload := map[string]interface{}{
		"id":                id,
		"memberId":          memberId,
		"surveyStatus":      "Ready to Survey",
		"surveyStatusCode":  2,
		"remarks":           "completed rotation",
		"surveyStatusAlert": "ready",
		"downloadDocument" : s3Url + S3filename,
	}
	_, _ = doPost(sreeraguUrl, payload)

	log.Printf("Writing final JSON to file")
	dataToWrite := []byte(response)
	err = os.WriteFile(Localjsonname, dataToWrite, 0644)
	if err != nil {
		log.Printf("Error writing JSON to file: %v", err)
	} else {
		log.Printf("Uploading final JSON to S3")
		UploadToS3(S3jsonname, Localjsonname)
		os.Remove(Localjsonname)
		log.Printf("Local JSON file removed")
	}
	
	log.Printf("Extractdata completed successfully for id: %s", id)
	return response
}

func GetPdf(id string, memberId string, data string) string {
	log.Printf("Starting GetPdf for id: %s, memberId: %s", id, memberId)
	
	response, err := Algs.Pycess(Algs.PyParam{
		Mod: "getPDF",
		Arg: []any{data},
	})
	if err != nil {
		log.Printf("Error in getPDF: %v", err)
		return `{"success": false, "Error": "getPDF", "message": "We are facing some technical issues, please try again or contact support","error": "` + err.Error() + `"}`
	}

	if response[0] != '!' {
		log.Printf("PDF generated successfully, uploading to S3")
		done := UploadToS3(s3satPdfDir + memberId + "/" + id+".pdf", response)
		if !done {
			log.Printf("Error uploading PDF to S3")
			return `{"success": false, "Error": "upload to s3", "message": "We are facing some technical issues, please try again or contact support","error": "` + err.Error() + `"}`
		}
		log.Printf("PDF uploaded to S3 successfully")
	}else{
		log.Printf("PDF generation failed: %s", response)
		payload := map[string]interface{}{
			"id":                id,
			"memberId":          memberId,
			"surveyStatus":      "Processing",
			"surveyStatusCode":  1,
			"remarks":           response,
			"surveyStatusAlert": PdfGenError,
		}
		_, _ = doPost(sreeraguUrl, payload)
		return `{"success": false, "Error": "getPDF", "message": "We are facing some technical issues, please try again or contact support","error": "` + response + `"}`
	}
	
	response = s3Url + s3satPdfDir + memberId + "/" + id + ".pdf"
	log.Printf("PDF URL: %s", response)
	
	payload := map[string]interface{}{
		"id":                id,
		"memberId":          memberId,
        "editedPDF": response,
        "surveyStatus": "Completed",
        "surveyStatusCode": 3,
        "remarks": "downloaded pdf",
	}
	_, _ = doPost(sreeraguUrl, payload)

	log.Printf("Cleaning up temporary PDF files")
	os.Remove(pdfTempDir + id + ".pdf")
	os.Remove(pdfTempDir + id + "_1.pdf")
	os.Remove(pdfTempDir + id + "_2.pdf")
	os.Remove(pdfTempDir + id + ".svg")

	log.Printf("GetPdf completed successfully for id: %s", id)
	return response
}

func GetRotatedCoords(content string) string {
	log.Printf("Starting GetRotatedCoords")
	
	response, err := Algs.Pycess(Algs.PyParam{
		Mod: "getRotatedCoords",
		Arg: []any{content},
	})
	if err != nil || response[0] == '!' {
		log.Printf("Error in getRotatedCoords: %v", err)
		return `{"success": false, "Error": "getRotatedCoords", "message": "We are facing some technical issues, please try again later","error": "` + err.Error() + `"}`
	}
	
	log.Printf("GetRotatedCoords completed successfully")
	return response
}

func UpdateData(content string) string {
	log.Printf("Starting UpdateData")
	
	response, err := Algs.Pycess(Algs.PyParam{
		Mod: "updateData",
		Arg: []any{content},
	})
	if err != nil {
		log.Printf("Error in updateData: %v", err)
		return `{"success": false, "Error": "updateData", "message": "We are facing some technical issues, please try again later","error": "` + err.Error() + `"}`
	}
	
	log.Printf("UpdateData completed successfully")
	return response
}

func Selectand_rotate_coords(content string) string {
	log.Printf("Starting Selectand_rotate_coords")
	
	response, err := Algs.Pycess(Algs.PyParam{
		Mod: "selectand_rotate_coords",
		Arg: []any{content},
	})
	if err != nil || response[0] == '!' {
		log.Printf("Error in selectand_rotate_coords: %v", err)
		return `{"success": false, "Error": "selectand_rotate_coords", "message": "We are facing some technical issues, please try again later","error": "` + err.Error() + `"}`
	}
	
	log.Printf("Selectand_rotate_coords completed successfully")
	return response
}

func UpdateFromKml(content string) string {
	log.Printf("Starting UpdateFromKml")

	response, err := Algs.Pycess(Algs.PyParam{
		Mod: "updateFromKml",
		Arg: []any{content},
	})

	if err != nil || response[0] == '!' {
		log.Printf("Error in updateFromKml: %v", err)
		return `{"success": false, "Error": "updateFromKml", "message": "We are facing some technical issues, please try again later","error": "` + err.Error() + `"}`
	}

	var data map[string]interface{}
	err = json.Unmarshal([]byte(content), &data)
	if err != nil {
		log.Printf("Error unmarshaling content in UpdateFromKml: %v", err)
		return `{"success": false, "Error": "updateFromKml", "message": "Failed to unmarshal content","error": "` + err.Error() + `"}`
	}

	district := data["district"].(string)
	taluk := data["taluk"].(string)
	village := data["village"].(string)
	survey_no := data["survey_no"].(string)

	Localjsonname := strings.ReplaceAll(outputDir+"FromKml/"+district+taluk+village+survey_no+".json", " ", "_")
	S3jsonname := strings.ReplaceAll(s3jsonDir+district+taluk+village+survey_no+".json", " ", "_")

	dir := filepath.Dir(Localjsonname)
	if err := os.MkdirAll(dir, 0755); err != nil {
		log.Printf("Error creating directory %s: %v", dir, err)
		return `{"success": false, "Error": "updateFromKml", "message": "Failed to create directory for file","error": "` + err.Error() + `"}`
	}

	err = os.WriteFile(Localjsonname, []byte(response), 0644)
	if err != nil {
		log.Printf("Error writing response to file %s: %v", Localjsonname, err)
		return `{"success": false, "Error": "updateFromKml", "message": "Failed to write response to file","error": "` + err.Error() + `"}`
	}

	UploadToS3(S3jsonname, Localjsonname)
	os.Remove(Localjsonname)
	fmt.Println("S3jsonname", S3jsonname)
	log.Printf("UpdateFromKml completed successfully")
	return response
}