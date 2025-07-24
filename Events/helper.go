package Events

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mypropertyqr-landsurvey/Algs"
	"net/http"
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

func getLandDetails(id, Mid string){

}

func getA0(){
	
}

func Extractdata(id, Mid string){
	response := Algs.Pycess(Algs.PyParam{
		Mod: "ExtractPdf",
		Arg: []any{"4.pdf"},
	})

	var res Algs.PyRes
	err := json.Unmarshal([]byte(response), &res)
	if err != nil {
		fmt.Println("JSON error:", err)
		return
	}

	res.Line3 = Algs.RemoveFloatingLines(res.Line3)
	newLine1 := Algs.RemoveFloatingLines(res.Line1)


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
	for _, seg := range newLine1 {
		for _, p := range seg {
			key := fmt.Sprintf("%.2f_%.2f", p[0], p[1])
			if !seen[key] {
				seen[key] = true
				points = append(points, Algs.Point{p[0], p[1]})
			}
		}
	}
    //all red text with coordinates ((x,y):text)    
	CoordRed := Algs.RankBasedAssignment(points, res.R)
    CoordBlue := Algs.FormatBbox(res.B)

    CoordRedMap := make(map[Algs.Point]string)
    for key, value := range CoordRed {
        CoordRedMap[value] = key
    }

    // get subdiv
    str, err := json.Marshal([]any{CoordBlue, res.Line1, res.Line3, res.Xmax - res.Xmin, res.Ymax - res.Ymin})
    if err != nil {
        fmt.Println("Error marshaling Line1 to JSON:", err)
    }
    response = Algs.Pycess(Algs.PyParam{
		Mod: "getSubdiv",
		Arg: []any{string(str)},
	})

    var subdivResult map[string][][][]float32
    err = json.Unmarshal([]byte(response), &subdivResult)
    if err != nil {
        fmt.Println("Error unmarshaling subdiv JSON:", err)
        return
    }


    for ind := range CoordBlue {
        subdivResult[ind] = Algs.OrderLines(subdivResult[ind])
    }


//remove line if dont have text
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

    // fmt.Println(subdivResult)   
    // fmt.Println((Algs.FlattenPoints(subdivResult["3"])))

	coordinates := make(map[string][]any)
	for c := range CoordRed {
		temp := CoordRed[c]
		coordinates[c] = []any{[]float32{temp.X, temp.Y}, "main", []string{"notmodified", "notmodified"}}
	}

	lines := make([]map[string]any, 0, len(res.Line3))
	for _, seg := range res.Line3 {
		lines = append(lines, map[string]any{
			"coordinates": []string{CoordRedMap[Algs.Point{seg[0][0], seg[0][1]}], CoordRedMap[Algs.Point{seg[1][0], seg[1][1]}]},
			"length":      Algs.Distance(Algs.Point{seg[0][0], seg[0][1]}, Algs.Point{seg[1][0], seg[1][1]}),
			"dashes":      "[ 9 0 ] 1",
			"strokewidth": "2",
		})
	}
	for _, subdivPolys := range subdivResult {
		for _, poly := range subdivPolys {
			for i := 0; i < len(poly)-1; i++ {
				start := poly[i]
				end := poly[i+1]
				lines = append(lines, map[string]any{
					"coordinates": []string{
						CoordRedMap[Algs.Point{start[0], start[1]}],
						CoordRedMap[Algs.Point{end[0], end[1]}],
					},
					"length":      Algs.Distance(Algs.Point{start[0], start[1]}, Algs.Point{end[0], end[1]}),
					"dashes":      "[ 30 10 1 3 1 3 1 10 ] 1",
					"strokewidth": "1",
				})
			}
		}
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

		if(len(flattenedArr) == 0){
			continue
		}

		grp = append(grp, []any{CoordBlue[key].X, CoordBlue[key].Y})
		grp = append(grp, flattenedArr)
		grp = append(grp, Algs.CalculateArea(flattened))

		subdiv_list[key] = grp
	}


	data, err := json.Marshal(map[string]any{"lines": lines, "subdivision_list": subdiv_list, "coordinates": coordinates, "scale": res.Scale})
	if err != nil {
		fmt.Println("Error marshaling lines:", err)
	}

	response = Algs.Pycess(Algs.PyParam{
		Mod: "shrink_or_expand_points",
		Arg: []any{string(data)},
	})

	// data, err = json.Marshal(response)
	// if err != nil {
	// 	fmt.Println("Error marshaling lines:", err)
	// }
	// response = Algs.Pycess(Algs.PyParam{
	// 	Mod: "rapidProcess",
	// 	Arg: []any{string(data)},
	// })

	fmt.Println(response)
}

// func getA0(){

// }

// func Extractdata(id, Mid string) map[string]interface{} {

// 	payload := map[string]string{
// 		"id":       id,
// 		"memberId": Mid,
// 	}

// 	dep1, err := doPost("https://prod-api.sreeragu.com/api/v2/MobileSurvey/getById", payload)
// 	if err != nil {
// 		return dep1
// 	}
// 	district := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["district"].(map[string]interface{})["name"])
// 	taluk := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["taluk"].(map[string]interface{})["name"])
// 	village := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["village"].(map[string]interface{})["name"])
// 	survey_no := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["surveyNumber"])
// 	noOfSubdivision := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["noOfSubdivision"])
// 	latitude := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["latitude"])
// 	longitude := fmt.Sprintf("%v", dep1["data"].(map[string]interface{})["longitude"])

// 	dep2, err := doPost("https://survey.mypropertyqr.in/village/?lat="+latitude+"&lon="+longitude,payload)
// 	if err != nil {
// 		return dep2
// 	}
	
// 	inputfilename := district + taluk + village + survey_no
// 	inputfilename = strings.ReplaceAll(inputfilename, " ", "_")
// 	inputpdf := inputfilename + ".pdf"



// 	fmt.Println(district,taluk,village,survey_no,noOfSubdivision,inputpdf)
// 	return dep2
// }

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
