from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field, validator
from enum import Enum

app = FastAPI(title="BMI Calculator API")


class BMIUnits(str, Enum):
    metric = "metric"
    imperial = "imperial"


class BMIInput(BaseModel):
    weight: float = Field(..., gt=0, description="Weight in kg (metric) or lbs (imperial)")
    height: float = Field(..., gt=0, description="Height in cm (metric) or inches (imperial)")
    units: BMIUnits = Field(default=BMIUnits.metric, description="Unit system")

    @validator("weight", "height")
    def positive_value(cls, v):
        if v <= 0:
            raise ValueError("must be positive")
        return v


class BMICategory(str, Enum):
    underweight = "Underweight"
    normal = "Normal weight"
    overweight = "Overweight"
    obese = "Obese"


class BMIResult(BaseModel):
    bmi: float = Field(..., description="Calculated BMI value")
    category: BMICategory = Field(..., description="BMI category")
    weight_kg: float = Field(..., description="Weight in kilograms")
    height_m: float = Field(..., description="Height in meters")


def calculate_bmi(weight_kg: float, height_m: float) -> tuple[float, BMICategory]:
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = BMICategory.underweight
    elif bmi < 25:
        category = BMICategory.normal
    elif bmi < 30:
        category = BMICategory.overweight
    else:
        category = BMICategory.obese

    return round(bmi, 1), category


@app.post("/bmi/calculate", response_model=BMIResult)
def calculate_bmi_endpoint(input_data: BMIInput):
    if input_data.units == BMIUnits.metric:
        weight_kg = input_data.weight
        height_m = input_data.height / 100
    else:
        weight_kg = input_data.weight * 0.453592
        height_m = input_data.height * 0.0254

    if height_m <= 0 or weight_kg <= 0:
        raise HTTPException(status_code=400, detail="Invalid converted values")

    bmi, category = calculate_bmi(weight_kg, height_m)

    return BMIResult(
        bmi=bmi,
        category=category,
        weight_kg=round(weight_kg, 2),
        height_m=round(height_m, 2)
    )


@app.get("/bmi/{weight}/{height}")
def calculate_bmi_get(
    weight: float = Query(..., gt=0, description="Weight in kg"),
    height: float = Query(..., gt=0, description="Height in cm")
):
    weight_kg = weight
    height_m = height / 100

    bmi, category = calculate_bmi(weight_kg, height_m)

    return {
        "bmi": bmi,
        "category": category.value,
        "weight_kg": round(weight_kg, 2),
        "height_m": round(height_m, 2)
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
