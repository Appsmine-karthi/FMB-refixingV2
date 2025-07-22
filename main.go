package main


import (
    "fmt"
    "encoding/json"
	"mypropertyqr-landsurvey/Algs"
)



func main() {
	Algs.InitPy()


	response := Algs.Pycess(Algs.PyParam{
		Mod: "ExtractPdf",
		Arg: []any{"source.pdf"},
	})

	var res Algs.PyRes
	err := json.Unmarshal([]byte(response), &res)
	if err != nil {
		fmt.Println("JSON error:", err)
		return
	}

	res.Line3 = Algs.RemoveFloatingLines(res.Line3)

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
    //all red text with coordinates ((x,y):text)    
	CoordRed := Algs.RankBasedAssignment(points, res.R)
	fmt.Println(CoordRed)


}