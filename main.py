from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field, validator
from enum import Enum

app = FastAPI(title="BMI Calculator API")


class BMIUnits(str, Enum):
    metric = "metric"
    imperial = "imperial"


class Gender(str, Enum):
    male = "male"
    female = "female"


class BodyFatCategory(str, Enum):
    essential = "Essential Fat"
    athletes = "Athletes"
    fitness = "Fitness"
    average = "Average"
    obese = "Obese"


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


class BodyFatInput(BaseModel):
    weight: float = Field(..., gt=0, description="Weight in kg (metric) or lbs (imperial)")
    height: float = Field(..., gt=0, description="Height in cm (metric) or inches (imperial)")
    age: int = Field(..., gt=0, description="Age in years")
    gender: Gender = Field(..., description="Gender")
    units: BMIUnits = Field(default=BMIUnits.metric, description="Unit system")


class BodyFatResult(BaseModel):
    body_fat_percentage: float = Field(..., description="Estimated body fat percentage")
    category: BodyFatCategory = Field(..., description="Body fat category")
    fat_mass_kg: float = Field(..., description="Fat mass in kilograms")
    lean_mass_kg: float = Field(..., description="Lean body mass in kilograms")
    bmi: float = Field(..., description="BMI value")


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


def calculate_body_fat(weight_kg: float, height_m: float, age: int, gender: Gender) -> tuple[float, BodyFatCategory]:
    bmi = weight_kg / (height_m ** 2)

    if gender == Gender.male:
        body_fat = (1.20 * bmi) + (0.23 * age) - 16.2
    else:
        body_fat = (1.20 * bmi) + (0.23 * age) - 5.4

    body_fat = max(0, min(100, body_fat))
    fat_mass = weight_kg * (body_fat / 100)
    lean_mass = weight_kg - fat_mass

    if gender == Gender.male:
        if body_fat < 6:
            category = BodyFatCategory.essential
        elif body_fat < 14:
            category = BodyFatCategory.athletes
        elif body_fat < 18:
            category = BodyFatCategory.fitness
        elif body_fat < 25:
            category = BodyFatCategory.average
        else:
            category = BodyFatCategory.obese
    else:
        if body_fat < 14:
            category = BodyFatCategory.essential
        elif body_fat < 21:
            category = BodyFatCategory.athletes
        elif body_fat < 25:
            category = BodyFatCategory.fitness
        elif body_fat < 32:
            category = BodyFatCategory.average
        else:
            category = BodyFatCategory.obese

    return round(body_fat, 1), category, round(fat_mass, 2), round(lean_mass, 2)


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


@app.post("/bodyfat/calculate", response_model=BodyFatResult)
def calculate_body_fat_endpoint(input_data: BodyFatInput):
    if input_data.units == BMIUnits.metric:
        weight_kg = input_data.weight
        height_m = input_data.height / 100
    else:
        weight_kg = input_data.weight * 0.453592
        height_m = input_data.height * 0.0254

    if height_m <= 0 or weight_kg <= 0:
        raise HTTPException(status_code=400, detail="Invalid converted values")

    body_fat, category, fat_mass, lean_mass = calculate_body_fat(
        weight_kg, height_m, input_data.age, input_data.gender
    )
    bmi, _ = calculate_bmi(weight_kg, height_m)

    return BodyFatResult(
        body_fat_percentage=body_fat,
        category=category,
        fat_mass_kg=fat_mass,
        lean_mass_kg=lean_mass,
        bmi=bmi
    )
