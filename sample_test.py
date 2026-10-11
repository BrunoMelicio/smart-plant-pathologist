import os
from PIL import Image

from pathologist_engine import PlantPathologistClient


def run_test():
    print("=================================================================")
    print("  SMART PLANT PATHOLOGIST - TEST SUITE")
    print("  Model: moondream (1.8B VLM) on Apple Silicon Metal")
    print("=================================================================\n")

    client = PlantPathologistClient()

    test_cases = [
        ("static/samples/sample_healthy_monstera.jpg", "healthy", "Healthy"),
        ("static/samples/sample_iron_chlorosis.jpg", "chlorosis", "Moderate"),
        ("static/samples/sample_fungal_leaf_spot.jpg", "fungal", "High"),
        ("static/samples/sample_spider_mite_damage.jpg", "pest", "High"),
    ]

    for sample_file, key, expected_severity in test_cases:
        if not os.path.exists(sample_file):
            print(f"Skipping {sample_file} (not found)")
            continue

        print(f"▶ Testing Leaf Sample: {sample_file} (Key: {key})")
        img = Image.open(sample_file)

        # 1. Test with preset key
        result = client.diagnose_plant(img, preset_key=key)
        print(f"  Plant:       {result.plant_name}")
        print(f"  Status:      {result.health_status}")
        print(f"  Severity:    {result.severity}")
        print(f"  Primary:     {result.primary_issue}")
        print(f"  Symptoms:    {len(result.visual_symptoms)} identified")
        print(f"  Steps:       {len(result.remediation_steps)} action items")
        print(f"  Prognosis:   {result.prognosis}")
        print(f"  Moondream:   {result.raw_vision_analysis[:100]}...")

        assert result.severity == expected_severity
        assert len(result.remediation_steps) == 3
        print("  ✔ Preset Diagnosis PASS\n")

    # 2. Test raw unhinted image (simulating user uploading a photo)
    print("▶ Testing Dynamic User Upload (Unhinted Image: sample_fungal_leaf_spot.jpg)")
    unhinted_img = Image.open("static/samples/sample_fungal_leaf_spot.jpg")
    dynamic_res = client.diagnose_plant(unhinted_img, preset_key=None)
    print(f"  Dynamic Plant:   {dynamic_res.plant_name}")
    print(f"  Dynamic Status:  {dynamic_res.health_status}")
    print(f"  Dynamic Issue:   {dynamic_res.primary_issue}")
    print(f"  Symptoms:        {dynamic_res.visual_symptoms[0]}")
    print(f"  Step 1:          {dynamic_res.remediation_steps[0]}")
    assert dynamic_res.severity in ["Moderate", "High", "Critical"]
    print("  ✔ Dynamic Upload Diagnosis PASS\n")

    print("✔ All Plant Pathologist test scenarios passed successfully!")


if __name__ == "__main__":
    run_test()
