"""
EcoQuest is a web app designed to encourage eco-friendly habits. 
I focused on the backend feature for tracking plant-based meals, which handles POST and GET requests and calculates reduced CO2 emissions through plant-based eating. 
Below is the view related to the API endpoint for meal tracking at http://127.0.0.1:8000/api/eco-meals.
"""

import math
from typing import Dict

from rest_framework import generics

from .models import Profile, EcoMeals
from .serializers import EcoMealsSerializer

# Points awarded for every 100 grams of CO2 emissions reduced 
POINTS_AWARDED_100GCO2 = 50

# Conversion factor for CO2 emissions reduced to points
CO2_REDUCTION_FACTOR = 100


# Pre-determined values of total carbon footprint in g CO2-equivalent
CO2E_PLANTBASED_BREAKFAST_GRAMS = 1100
CO2E_PLANTBASED_LUNCH_GRAMS = 980
CO2E_PLANTBASED_DINNER_GRAMS = 1100

CO2E_MEATBASED_BREAKFAST_GRAMS = 2600
CO2E_MEATBASED_LUNCH_GRAMS = 3800
CO2E_MEATBASED_DINNER_GRAMS = 4800


class EcoMealsView(generics.ListCreateAPIView):

    """
    API view for retrieving and creating EcoMeals instances.
    Each EcoMeals instance represents one meal (either breakfast, lunch, or dinner) per user submission.

    This view supports listing all EcoMeals instances or creating a new instance.
    It includes methods for calculating CO2 emissions reduced from opting for plant-based meals and updating user points.

    Methods:
        get_queryset: Returns a record of all EcoMeals instances.
        perform_create: Saves a new EcoMeals instance and updates user profile with CO2 reductions and points.
        calculate_co2_reduced: Calculates CO2 emissions reduction based on meal choices.
        calculate_ecomeals_points: Calculates points earned based on CO2 reductions.
        update_user_profile: Updates the user's profile with new points and CO2 reductions.
    """

    serializer_class = EcoMealsSerializer

    def get_queryset(self):
        """
        Retrieves all EcoMeals instances currently stored in the database.

        Returns:
            A list of dictionaries. Each dictionary represents an EcoMeals instance.
        """
        return EcoMeals.objects.all()

    def perform_create(self, serializer: EcoMealsSerializer) -> None:
        """
        Create a new EcoMeals instance.

        Saves the instance with details from the POST request, calculates CO2 reductions
        and points to be awarded, as well as updates the user's profile accordingly.

        Parameters:
            serializer (EcoMealsSerializer): Parses and validates data from the POST request.
                                            Also responsible for creating a new EcoMeals instance.
        Raises:
            Exception: Prints an error message if creating an instance fails.
        """
        try:
            user = serializer.validated_data["user"]
            eco_breakfast = serializer.validated_data["eco_breakfast"]
            eco_lunch = serializer.validated_data["eco_lunch"]
            eco_dinner = serializer.validated_data["eco_dinner"]
            serializer.save(
                eco_breakfast=eco_breakfast, eco_lunch=eco_lunch, eco_dinner=eco_dinner
            )

            user_ecomeals_input = self.request.data
            co2_reduced = self.calculate_co2_reduced(user_ecomeals_input)
            ecomeals_points = self.calculate_ecomeals_points(co2_reduced)

            # Update EcoMeals instance with co2_reduced and ecomeals_points results
            eco_meals_instance = serializer.instance
            eco_meals_instance.co2_reduced = co2_reduced
            eco_meals_instance.ecomeals_points = ecomeals_points
            eco_meals_instance.save()

            # Update Profile with points from EcoMeals
            self.update_user_profile(user, co2_reduced, ecomeals_points)
        except Exception as e:
            print("An error has occurred: {e}")

    def calculate_co2_reduced(self, user_ecomeals_input: Dict[str, bool]) -> int:
        """
        Calculate the CO2 emissions reduced by choosing a plant-based meal.

        Based on the user's meal choice, this calculates the difference in CO2 emissions
        between the plant-based and meat-based version.

        Parameters:
            user_ecomeals_input (dict): Contains boolean values that show whether the user
                                        selected the plant-based option for breakfast, lunch, or dinner.

        Returns:
            co2_reduced (int): The total CO2 reduced (in grams) as a result of selecting plant-based options.
        """
        co2_reduced = 0

        if user_ecomeals_input["eco_breakfast"]:
            co2_reduced = (
                CO2E_MEATBASED_BREAKFAST_GRAMS - CO2E_PLANTBASED_BREAKFAST_GRAMS
            )

        elif user_ecomeals_input["eco_lunch"]:
            co2_reduced = CO2E_MEATBASED_LUNCH_GRAMS - CO2E_PLANTBASED_LUNCH_GRAMS

        elif user_ecomeals_input["eco_dinner"]:
            co2_reduced = CO2E_MEATBASED_DINNER_GRAMS - CO2E_PLANTBASED_DINNER_GRAMS

        return co2_reduced

    def calculate_ecomeals_points(self, user_co2_reduced: int) -> int:
        """
        Calculate points earned based on CO2 reductions.

        Points are awarded for every 100g of CO2 reduced, encouraging more sustainable eating habits.

        Parameters:
            user_co2_reduced (int): The total CO2 reduced (in grams) as a result of selecting plant-based options.

        Returns:
            ecomeals_points (int): The total of points earned.
        """
        ecomeals_points = math.floor(user_co2_reduced / 100 * POINTS_AWARDED_100GCO2)

        return ecomeals_points

    def update_user_profile(self, user: str, user_co2_reduced: int, user_ecomeals_points: int) -> None:
        """
        Update the user's profile with points and CO2 reductions from EcoMeals.

        Parameters:
            user (str): Represents the username of the user currently adding their ecomeal activity.
            user_co2_reduced (int): The total CO2 reduced (in grams) as a result of selecting plant-based options.
            user_eomeals_points (int): The total of points earned.
        """
        profile = Profile.objects.get(username=user)
        profile.total_co2e_reduced += user_co2_reduced
        profile.total_points += user_ecomeals_points
        profile.save()
