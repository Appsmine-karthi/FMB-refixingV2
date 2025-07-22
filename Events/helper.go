package Events

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mypropertyqr-landsurvey/Algs"
	"net/http"
	"strings"
)

func doPost(url string, body map[string]string) (map[string]interface{}, error) {

	bodyBytes, err := json.Marshal(body)
	if err != nil {
		panic(err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(bodyBytes))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		response := map[string]interface{}{"error": resp.StatusCode, "link": url, "payload": body}
		return response, fmt.Errorf("received non-200 response: %d", resp.StatusCode)
	}

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	err = json.Unmarshal(respBody, &result)
	if err != nil {
		fmt.Println(err)
		response := map[string]interface{}{"error": "error in unmarshalling","link":url,"payload":body}
		return response, fmt.Errorf("received non-200 response: %d", resp.StatusCode)
	}

	return result, nil
}

func getA0(){

}

func Extractdata(id, Mid string) map[string]interface{} {

	payload := map[string]string{
		"id":       id,
		"memberId": Mid,
	}

	dep1, err := doPost("https://prod-api.sreeragu.com/api/v2/MobileSurvey/getById", payload)
	if err != nil {
		return dep1
	}
	district := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["district"].(map[string]interface{})["name"])
	taluk := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["taluk"].(map[string]interface{})["name"])
	village := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["village"].(map[string]interface{})["name"])
	survey_no := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["surveyNumber"])
	noOfSubdivision := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["noOfSubdivision"])
	latitude := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["latitude"])
	longitude := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["longitude"])

	dep2, err := doPost("https://survey.mypropertyqr.in/village/?lat="+latitude+"&lon="+longitude,payload)
	if err != nil {
		return dep2
	}
	
	inputfilename := district + taluk + village + survey_no
	inputfilename = strings.ReplaceAll(inputfilename, " ", "_")
	inputpdf := inputfilename + ".pdf"



	fmt.Println(district,taluk,village,survey_no,noOfSubdivision,inputpdf)
	return dep2
}

// func Process() {
// 	response := Algs.Pycess(Algs.PyParam{
// 		Mod: "ExtractPdf",
// 		Arg: []any{"source.pdf"},
// 	})

// 	var res Algs.PyRes
// 	err := json.Unmarshal([]byte(response), &res)
// 	if err != nil {
// 		fmt.Println("JSON error:", err)
// 		return
// 	}

// 	res.Line3 = Algs.RemoveFloatingLines(res.Line3)

// 	seen := make(map[string]bool)
// 	var points []Algs.Point

// 	for _, seg := range res.Line3 {
// 		for _, p := range seg {
// 			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
// 			if !seen[key] {
// 				seen[key] = true
// 				points = append(points, Algs.Point{p[0], p[1]})
// 			}
// 		}
// 	}

// 	closest := Algs.RankBasedAssignment(points, res.R)
// 	fmt.Println(closest)
// }
