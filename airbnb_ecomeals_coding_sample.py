"""
EcoQuest is a web app designed to encourage eco-friendly habits. 
I focused on the backend feature for tracking plant-based meals, which handles POST and GET requests and calculates reduced carbon dioxide emissions through plant-based eating. 
Below is the view related to the API endpoint for meal tracking at http://127.0.0.1:8000/api/eco-meals.
"""

import math

from rest_framework import generics

from .ecomeals_models import EcoMeals
from .ecomeals_serializer import EcoMealsSerializer


POINTS_AWARDED_100GCO2 = 50

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

    - get_queryset: Returns a record of all EcoMeals instances.
    - perform_create: Saves a new EcoMeals instance and updates user profile with CO2 reductions and points.
    - calculate_co2_reduced: Calculates CO2 emissions reduction based on meal choices.
    - calculate_ecomeals_points: Calculates points earned based on CO2 reductions.
    - update_user_profile: Updates the user's profile with new points and CO2 reductions.
    """

    serializer_class = EcoMealsSerializer

    def get_queryset(self):
        """Return a queryset of all EcoMeals instances."""
        return EcoMeals.objects.all()

    def perform_create(self, serializer):
        """
        Create a new EcoMeals instance.

        Saves the instance with details from the POST request, calculates CO2 reductions
        and points to be awarded, as well as updates the user's profile accordingly.
        """
        try:
            user = serializer.validated_data["user"]
            eco_breakfast = serializer.validated_data["eco_breakfast"]
            eco_lunch = serializer.validated_data["eco_lunch"]
            eco_dinner = serializer.validated_data["eco_dinner"]
            serializer.save(
                eco_breakfast=eco_breakfast, eco_lunch=eco_lunch, eco_dinner=eco_dinner
            )

            co2_reduced = self.calculate_co2_reduced(self.request.data)
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

    def calculate_co2_reduced(self, user_ecomeals_input):
        """
        Calculate the CO2 emissions reduced by choosing a plant-based meal.

        Based on the user's meal choice, this calculates the difference in CO2 emissions
        between the plant-based and meat-based version.
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

    def calculate_ecomeals_points(self, user_co2_reduced):
        """
        Calculate points earned based on CO2 reductions.

        Points are awarded for every 100g of CO2 reduced, encouraging more sustainable eating habits.
        """
        ecomeals_points = math.floor(user_co2_reduced / 100 * POINTS_AWARDED_100GCO2)

        return ecomeals_points

    def update_user_profile(self, user, user_co2_reduced, user_ecomeals_points):
        """
        Update the user's profile with points and CO2 reductions from EcoMeals.
        """
        profile = Profile.objects.get(username=user)
        profile.total_co2e_reduced += user_co2_reduced
        profile.total_points += user_ecomeals_points
        profile.save()
