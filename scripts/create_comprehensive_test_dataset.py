#!/usr/bin/env python3
"""
Create comprehensive test dataset for end-to-end validation.

This script generates a strategic 50-lead test dataset covering all ethnicities
and Enhancement 2 validation cases for comprehensive system testing.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

def create_test_dataset() -> pd.DataFrame:
    """Create strategic 50-lead test dataset."""
    
    # Enhancement 2 validation cases (5 leads) - CRITICAL
    enhancement2_cases = [
        {
            "EntityName": "Van Der Merwe Holdings (Pty) Ltd",
            "TradingAsName": "VDM Holdings",
            "Keyword": "Property Development",
            "ContactNumber": "021-555-0001",
            "CellNumber": "082-123-4501",
            "EmailAddress": "info@vdmholdings.co.za",
            "RegisteredAddress": "12 Main Road",
            "RegisteredAddressCity": "Cape Town",
            "RegisteredAddressProvince": "Western Cape",
            "DirectorName": "ANDREAS PETRUS VAN DER MERWE",
            "DirectorCell": "082-123-4501"
        },
        {
            "EntityName": "Timmie Consulting CC",
            "TradingAsName": "TC Consulting",
            "Keyword": "Business Consulting",
            "ContactNumber": "011-555-0002",
            "CellNumber": "083-123-4502",
            "EmailAddress": "heinrich@tcconsulting.co.za",
            "RegisteredAddress": "45 Business Park Drive",
            "RegisteredAddressCity": "Johannesburg",
            "RegisteredAddressProvince": "Gauteng",
            "DirectorName": "HEINRICH ADRIAN TIMMIE",
            "DirectorCell": "083-123-4502"
        },
        {
            "EntityName": "Msindo Community Services",
            "TradingAsName": "MCS",
            "Keyword": "Community Development",
            "ContactNumber": "043-555-0003",
            "CellNumber": "072-123-4503",
            "EmailAddress": "nomvuyiseko@mcs.org.za",
            "RegisteredAddress": "22 Township Road",
            "RegisteredAddressCity": "East London",
            "RegisteredAddressProvince": "Eastern Cape",
            "DirectorName": "NOMVUYISEKO EUNICE MSINDO",
            "DirectorCell": "072-123-4503"
        },
        {
            "EntityName": "Pietersen Holdings",
            "TradingAsName": "PH Investments",
            "Keyword": "Investment Management",
            "ContactNumber": "031-555-0004",
            "CellNumber": "084-123-4504",
            "EmailAddress": "allister@phinvestments.co.za",
            "RegisteredAddress": "88 Marine Parade",
            "RegisteredAddressCity": "Durban",
            "RegisteredAddressProvince": "KwaZulu-Natal",
            "DirectorName": "ALLISTER PIETERSEN",
            "DirectorCell": "084-123-4504"
        },
        {
            "EntityName": "Majibane Development Trust",
            "TradingAsName": "MDT",
            "Keyword": "Rural Development",
            "ContactNumber": "047-555-0005",
            "CellNumber": "073-123-4505",
            "EmailAddress": "mncedi@mdt.org.za",
            "RegisteredAddress": "15 Village Square",
            "RegisteredAddressCity": "Mthatha",
            "RegisteredAddressProvince": "Eastern Cape",
            "DirectorName": "MNCEDI NICHOLAS MAJIBANE",
            "DirectorCell": "073-123-4505"
        }
    ]
    
    # Learning database test cases (3 leads)
    learning_cases = [
        {
            "EntityName": "Botha Construction",
            "TradingAsName": "BC Construction",
            "Keyword": "Construction",
            "ContactNumber": "012-555-0006",
            "CellNumber": "082-123-4506",
            "EmailAddress": "johannes@bconstruction.co.za",
            "RegisteredAddress": "34 Industrial Avenue",
            "RegisteredAddressCity": "Pretoria",
            "RegisteredAddressProvince": "Gauteng",
            "DirectorName": "JOHANNES BOTHA",
            "DirectorCell": "082-123-4506"
        },
        {
            "EntityName": "Papa Logistics",
            "TradingAsName": "Papa Transport",
            "Keyword": "Logistics",
            "ContactNumber": "051-555-0007",
            "CellNumber": "074-123-4507",
            "EmailAddress": "siyabulela@papalogistics.co.za",
            "RegisteredAddress": "67 Transport Hub",
            "RegisteredAddressCity": "Bloemfontein",
            "RegisteredAddressProvince": "Free State",
            "DirectorName": "SIYABULELA PAPA",
            "DirectorCell": "074-123-4507"
        },
        {
            "EntityName": "TestName Innovations",
            "TradingAsName": "TNI",
            "Keyword": "Technology",
            "ContactNumber": "018-555-0008",
            "CellNumber": "075-123-4508",
            "EmailAddress": "unknown@testinnovations.co.za",
            "RegisteredAddress": "99 Tech Park",
            "RegisteredAddressCity": "Klerksdorp",
            "RegisteredAddressProvince": "North West",
            "DirectorName": "UNKNOWN TESTNAME NEWPATTERN",
            "DirectorCell": "075-123-4508"
        }
    ]
    
    # Edge cases (2 leads)
    edge_cases = [
        {
            "EntityName": "Van Der Walt Family Trust",
            "TradingAsName": "VDWFT",
            "Keyword": "Trust Management",
            "ContactNumber": "013-555-0009",
            "CellNumber": "076-123-4509",
            "EmailAddress": "pieter@vdwft.co.za",
            "RegisteredAddress": "123 Trust Avenue",
            "RegisteredAddressCity": "Nelspruit",
            "RegisteredAddressProvince": "Mpumalanga",
            "DirectorName": "PIETER JOHANNES VAN DER WALT JUNIOR",
            "DirectorCell": "076-123-4509"
        },
        {
            "EntityName": "Adams-Hendricks Enterprises",
            "TradingAsName": "AHE",
            "Keyword": "Trading",
            "ContactNumber": "021-555-0010",
            "CellNumber": "077-123-4510",
            "EmailAddress": "fatima@ahe.co.za",
            "RegisteredAddress": "56 Commerce Street",
            "RegisteredAddressCity": "Cape Town",
            "RegisteredAddressProvince": "Western Cape",
            "DirectorName": "FATIMA KHADIJA ADAMS-HENDRICKS",
            "DirectorCell": "077-123-4510"
        }
    ]
    
    # White names (10 leads) - 5 Afrikaans compound, 5 English
    white_names = [
        # Afrikaans compound names
        ("Du Plessis Farming", "DP Farming", "Agriculture", "FRANCOIS DU PLESSIS"),
        ("De Beer Holdings", "DB Holdings", "Mining", "HENDRIK DE BEER"),
        ("Le Roux Attorneys", "LR Legal", "Legal Services", "MARIA LE ROUX"),
        ("Van Rensburg Consulting", "VR Consulting", "Management", "JOHAN VAN RENSBURG"),
        ("Du Toit Engineering", "DT Engineering", "Engineering", "PETRUS DU TOIT"),
        
        # English names
        ("Smith & Associates", "Smith Legal", "Legal", "DAVID SMITH"),
        ("Johnson Investments", "JI Holdings", "Finance", "MICHAEL JOHNSON"),
        ("Williams Manufacturing", "WM Industries", "Manufacturing", "SARAH WILLIAMS"),
        ("Brown Properties", "BP Real Estate", "Property", "ANDREW BROWN"),
        ("Taylor Consulting", "TC Services", "Consulting", "EMMA TAYLOR")
    ]
    
    # African names (10 leads) - 4 Xhosa, 3 Zulu, 3 Sotho/Tswana
    african_names = [
        # Xhosa names
        ("Mthembu Trading", "MT", "Trading", "SIPHO MTHEMBU"),
        ("Nkomo Development", "ND", "Development", "NOMSA NKOMO"),
        ("Dlamini Transport", "DT", "Transport", "THEMBA DLAMINI"),
        ("Gumede Services", "GS", "Services", "ZANELE GUMEDE"),
        
        # Zulu names
        ("Mokwena Holdings", "MH", "Holdings", "LERATO MOKWENA"),
        ("Molefe Enterprises", "ME", "Business", "TEBOGO MOLEFE"),
        ("Mabena Construction", "MC", "Construction", "KGOMOTSO MABENA"),
        
        # Sotho/Tswana names
        ("Mokoena Suppliers", "MS", "Supply Chain", "THABO MOKOENA"),
        ("Khumalo Industries", "KI", "Manufacturing", "BUSISIWE KHUMALO"),
        ("Radebe Consulting", "RC", "Consulting", "MANDLA RADEBE")
    ]
    
    # Indian names (8 leads) - 4 Tamil, 2 Gujarati, 2 Hindi
    indian_names = [
        # Tamil names
        ("Patel Spices", "PS", "Food", "RAVI PATEL"),
        ("Naidoo Textiles", "NT", "Textiles", "PRIYA NAIDOO"),
        ("Reddy Motors", "RM", "Automotive", "SURESH REDDY"),
        ("Pillay Imports", "PI", "Import/Export", "KAVITHA PILLAY"),
        
        # Gujarati names
        ("Shah Jewellers", "SJ", "Jewellery", "AMIT SHAH"),
        ("Desai Properties", "DP", "Property", "MEERA DESAI"),
        
        # Hindi names
        ("Kumar Electronics", "KE", "Electronics", "RAJESH KUMAR"),
        ("Sharma Trading", "ST", "Trading", "DEEPA SHARMA")
    ]
    
    # Cape Malay names (6 leads)
    cape_malay_names = [
        ("Abdullah Fisheries", "AF", "Fishing", "MOHAMED ABDULLAH"),
        ("Samuels Bakery", "SB", "Food", "YASMIN SAMUELS"),
        ("Davids Catering", "DC", "Catering", "AHMED DAVIDS"),
        ("Fortune Spices", "FS", "Spices", "FATIMA FORTUNE"),
        ("Kamaldien Transport", "KT", "Transport", "HASSAN KAMALDIEN"),
        ("Isaacs Trading", "IT", "Trading", "AMINA ISAACS")
    ]
    
    # Coloured names (6 leads) - 3 month surnames, 3 other
    coloured_names = [
        # Month surnames
        ("April Holdings", "AH", "Holdings", "WAYNE APRIL"),
        ("September Enterprises", "SE", "Business", "CHANTELLE SEPTEMBER"),
        ("October Trading", "OT", "Trading", "BRADLEY OCTOBER"),
        
        # Other Coloured names
        ("Jantjies Services", "JS", "Services", "DEAN JANTJIES"),
        ("Philander Transport", "PT", "Transport", "ROCHELLE PHILANDER"),
        ("Sauls Construction", "SC", "Construction", "GARETH SAULS")
    ]
    
    # Helper function to create lead records
    def create_lead_record(company_info: tuple, base_phone: int, province: str) -> Dict[str, Any]:
        company_name, trading_name, industry, director = company_info
        return {
            "EntityName": company_name,
            "TradingAsName": trading_name,
            "Keyword": industry,
            "ContactNumber": f"0{(11 + base_phone % 10)}-555-{base_phone:04d}",
            "CellNumber": f"08{2 + base_phone % 7}-123-{base_phone:04d}",
            "EmailAddress": f"info@{trading_name.lower().replace(' ', '')}.co.za",
            "RegisteredAddress": f"{base_phone} Business Street",
            "RegisteredAddressCity": ["Cape Town", "Johannesburg", "Durban", "Pretoria", "Port Elizabeth"][base_phone % 5],
            "RegisteredAddressProvince": province,
            "DirectorName": director,
            "DirectorCell": f"08{2 + base_phone % 7}-123-{base_phone:04d}"
        }
    
    # Combine all test data
    all_leads = []
    
    # Add special test cases first
    all_leads.extend(enhancement2_cases)
    all_leads.extend(learning_cases)
    all_leads.extend(edge_cases)
    
    # Add ethnicity distribution cases
    phone_counter = 100
    provinces = ["Western Cape", "Gauteng", "KwaZulu-Natal", "Eastern Cape", "Free State", "Mpumalanga", "Limpopo", "North West", "Northern Cape"]
    
    for name_list in [white_names, african_names, indian_names, cape_malay_names, coloured_names]:
        for company_info in name_list:
            all_leads.append(create_lead_record(company_info, phone_counter, provinces[phone_counter % len(provinces)]))
            phone_counter += 1
    
    return pd.DataFrame(all_leads)

def main():
    """Create and save the comprehensive test dataset."""
    print("🚀 Creating Comprehensive Test Dataset")
    print("=" * 50)
    
    # Create dataset
    df = create_test_dataset()
    
    # Validate dataset
    print(f"✅ Created dataset with {len(df)} leads")
    print(f"✅ Enhancement 2 cases: 5")
    print(f"✅ Learning test cases: 3") 
    print(f"✅ Edge cases: 2")
    print(f"✅ Ethnicity distribution: 40")
    
    # Show ethnicity breakdown
    director_names = df['DirectorName'].tolist()
    print(f"\n📊 Sample director names:")
    for i, name in enumerate(director_names[:10]):
        print(f"  {i+1:2d}. {name}")
    
    # Save to Excel
    output_path = Path("data/test_runs/comprehensive_validation_test.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    
    print(f"\n💾 Saved test dataset to: {output_path}")
    print(f"✅ Ready for comprehensive validation testing")
    
    return output_path

if __name__ == "__main__":
    main()