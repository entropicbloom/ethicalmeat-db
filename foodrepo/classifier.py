"""LLM-based classification system for animal types and labels."""

import json
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Result of LLM classification."""
    animal: str
    label: str
    confidence: float
    reasoning: str


class ProductClassifier:
    """LLM-based classifier for animal types and Swiss meat labels."""

    # Allowed animal types (exactly matching EMH data)
    ALLOWED_ANIMALS = {
        'eier', 'kalbfleisch', 'milch', 'poulet', 'rindfleisch', 'schweinefleisch',
        'unknown'  # Keep unknown for fallback
    }

    # Swiss meat labels and programs (exactly matching EMH data)
    ALLOWED_LABELS = {
        'AGRI NATURA D', 'BIO NATUR PLUS D', 'BIO ORGANIC MIT SCHWEIZER KREUZ D',
        'BIO SUISSE / BIO KNOSPE D', 'BÜNDNER PUURACHALB D', 'COOP NATURAFARM D',
        'COOP NATURAPLAN D', 'Coop Milchprogramm D', 'Cowpassion D', 'DEMETER D',
        'Die Faire Milch', 'Fairmilk Aldi  D', 'Heidimilch D', 'Heumilch D',
        'IP-SUISSE D', 'KAGfreiland D', 'KRÄUTERSCHWEIN D',
        'MIGROS BIO MIT SCHWEIZERKREUZ D', 'MIGROS BIO OHNE SCHWEIZERKREUZ D',
        'MIGROS BIO WEIDE-BEEF D', 'MIGROS WEIDE-BEEF D', 'Migros nachhaltige Milch D',
        'Milch Grüner Teppich D', 'NATURA-BEEF D', 'NATURA-VEAL DE',
        'NATURE SUISSE BIO D', 'NATURE SUISSE D', 'OPTIGAL D', 'Pro Montagna D',
        'Retour aux sources D', 'SILVESTRI ALPSCHWEIN D', 'SILVESTRI BIO-WEIDERIND D',
        'SILVESTRI FREILANDSCHWEIN D', 'SILVESTRI WEIDERIND D', 'SUISSE GARANTIE D',
        'SWISS BLACK ANGUS D',
        'unknown'  # Keep unknown for fallback
    }

    # Simple rules to apply before LLM classification (updated for EMH values)
    # Note: Order matters! More specific patterns should come first
    ANIMAL_RULES = [
        # Animal detection rules (EMH German terms) - more specific first
        (re.compile(r'\bkalbfleisch\b', re.I), 'kalbfleisch'),
        (re.compile(r'\bkalb\b(?!fleisch)', re.I), 'kalbfleisch'),  # "kalb" but not "kalbfleisch"
        (re.compile(r'\b(veal|veau|vitello)\b', re.I), 'kalbfleisch'),
        (re.compile(r'\brindfleisch\b', re.I), 'rindfleisch'),
        (re.compile(r'\b(rind|beef|boeuf|manzo)\b', re.I), 'rindfleisch'),
        (re.compile(r'\bschweinefleisch\b', re.I), 'schweinefleisch'),
        (re.compile(r'\b(schwein|pork|porc|maiale)\b', re.I), 'schweinefleisch'),
        (re.compile(r'\b(poulet|huhn|chicken|pollo|hähnchen)\b', re.I), 'poulet'),
        # Be very specific with eggs - only match when clearly about eggs, not as substring
        (re.compile(r'\b(eier|eggs|oeufs|uova)\b', re.I), 'eier'),
        # Be very specific with milk - only standalone word
        (re.compile(r'\bmilch\b', re.I), 'milch'),
        (re.compile(r'\b(milk|lait|latte)\b(?!\s*chocolate)', re.I), 'milch'),
    ]

    LABEL_RULES = [
        # Label detection rules (exact EMH label matches) - more specific first
        (re.compile(r'\bnaturaplan\b', re.I), 'COOP NATURAPLAN D'),
        (re.compile(r'\bnatura[- ]?plan\b', re.I), 'COOP NATURAPLAN D'),
        (re.compile(r'\bnaturafarm\b', re.I), 'COOP NATURAFARM D'),
        (re.compile(r'\bnatura[- ]?farm\b', re.I), 'COOP NATURAFARM D'),
        (re.compile(r'\bnature suisse bio\b', re.I), 'NATURE SUISSE BIO D'),
        (re.compile(r'\bnature suisse\b', re.I), 'NATURE SUISSE D'),
        (re.compile(r'\bnatura[- ]?beef\b', re.I), 'NATURA-BEEF D'),
        (re.compile(r'\bnatura[- ]?veal\b', re.I), 'NATURA-VEAL DE'),
        (re.compile(r'\bbio suisse|bio knospe|knospe\b', re.I), 'BIO SUISSE / BIO KNOSPE D'),
        (re.compile(r'\bmigros.*bio.*weide[- ]?beef\b', re.I), 'MIGROS BIO WEIDE-BEEF D'),
        (re.compile(r'\bmigros.*weide[- ]?beef\b', re.I), 'MIGROS WEIDE-BEEF D'),
        (re.compile(r'\bmigros.*bio.*schweiz', re.I), 'MIGROS BIO MIT SCHWEIZERKREUZ D'),
        (re.compile(r'\bip[- ]?suisse\b', re.I), 'IP-SUISSE D'),
        (re.compile(r'\bsuisse\s*garantie\b', re.I), 'SUISSE GARANTIE D'),
        (re.compile(r'\bagri\s*natura\b', re.I), 'AGRI NATURA D'),
        (re.compile(r'\bdemeter\b', re.I), 'DEMETER D'),
        (re.compile(r'\bkag\s*freiland\b', re.I), 'KAGfreiland D'),
        (re.compile(r'\boptigal\b', re.I), 'OPTIGAL D'),
        (re.compile(r'\bsilvestri.*bio.*weiderind\b', re.I), 'SILVESTRI BIO-WEIDERIND D'),
        (re.compile(r'\bsilvestri.*weiderind\b', re.I), 'SILVESTRI WEIDERIND D'),
        (re.compile(r'\bsilvestri.*freiland\b', re.I), 'SILVESTRI FREILANDSCHWEIN D'),
        (re.compile(r'\bsilvestri.*alpschwein\b', re.I), 'SILVESTRI ALPSCHWEIN D'),
    ]

    def __init__(self, use_simple_rules: bool = True):
        """Initialize classifier.

        Args:
            use_simple_rules: Whether to apply simple regex rules before LLM
        """
        self.use_simple_rules = use_simple_rules

    def apply_simple_rules(self, product: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Apply simple regex rules to classify product.

        Args:
            product: Product dictionary

        Returns:
            Dictionary with 'animal' and/or 'label' keys if rules matched, None otherwise
        """
        if not self.use_simple_rules:
            return None

        # Combine text fields for pattern matching
        # Note: FoodRepo v3 API does not provide brands, but Open Food Facts enrichment may add them
        text_fields = [
            product.get('name', ''),
            product.get('brands', ''),  # May be added by Open Food Facts enrichment
            product.get('ingredients_text', '')[:200]  # Limit ingredients text length
        ]

        full_text = ' '.join(str(field) for field in text_fields if field)

        result = {}

        # Apply animal rules - STOP at first match (most specific wins)
        for pattern, value in self.ANIMAL_RULES:
            if pattern.search(full_text):
                result['animal'] = value
                break  # Stop at first match

        # Apply label rules - STOP at first match (most specific wins)
        for pattern, value in self.LABEL_RULES:
            if pattern.search(full_text):
                result['label'] = value
                break  # Stop at first match

        return result if result else None

    def classify_with_llm_prompt(self, product: Dict[str, Any]) -> str:
        """Generate LLM prompt for product classification.

        This method creates the prompt but doesn't actually call an LLM.
        You would integrate this with your preferred LLM service.

        Args:
            product: Product dictionary

        Returns:
            LLM prompt string
        """
        # Prepare product context
        context = {
            "name": product.get("name", ""),
            "brands": product.get("brands", []),
            "categories": product.get("categories", ""),
            "ingredients": (product.get("ingredients_text", "") or "")[:500],  # Limit length
            "origins": product.get("origins", []),
        }

        prompt = f"""You are a Swiss meat product classifier. Based on the product information below, classify the animal type and Swiss meat label/program.

Product Information:
- Name: {context['name']}
- Brands: {context['brands']}
- Categories: {context['categories']}
- Ingredients: {context['ingredients']}
- Origins: {context['origins']}

STRICT REQUIREMENTS:
1. Animal type must be one of: {', '.join(sorted(self.ALLOWED_ANIMALS))}
2. Label must be one of: {', '.join(sorted(self.ALLOWED_LABELS))}
3. Use "unknown" when evidence is insufficient
4. Focus on Swiss market labels and programs
5. Consider multilingual terms (German, French, Italian)

Return ONLY a JSON object with this exact format:
{{
    "animal": "one of the allowed animal types",
    "label": "one of the allowed labels",
    "confidence": 0.85,
    "reasoning": "Brief explanation of classification"
}}

Examples:
- "Poulet Migros" → {{"animal": "poulet", "label": "unknown", "confidence": 0.9, "reasoning": "Poulet indicates chicken, but no specific program identified"}}
- "Natura-Beef Entrecôte" → {{"animal": "rindfleisch", "label": "NATURA-BEEF D", "confidence": 0.95, "reasoning": "Clear Natura-Beef program for beef product"}}
- "Bio Kalbsschnitzel" → {{"animal": "kalbfleisch", "label": "unknown", "confidence": 0.8, "reasoning": "Kalb indicates veal, Bio suggests organic but no specific Swiss program"}}
"""

        return prompt

    def parse_llm_response(self, response_text: str) -> Optional[ClassificationResult]:
        """Parse LLM JSON response into ClassificationResult.

        Args:
            response_text: Raw LLM response text

        Returns:
            ClassificationResult or None if parsing failed
        """
        try:
            # Extract JSON from response (handle case where LLM adds extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                return None

            data = json.loads(json_match.group())

            # Validate required fields
            required_fields = ['animal', 'label', 'confidence', 'reasoning']
            if not all(field in data for field in required_fields):
                return None

            # Validate values are in allowed sets
            animal = data['animal'].lower()
            label = data['label'].lower()

            if animal not in self.ALLOWED_ANIMALS:
                animal = 'unknown'

            if label not in self.ALLOWED_LABELS:
                label = 'unknown'

            return ClassificationResult(
                animal=animal,
                label=label,
                confidence=float(data['confidence']),
                reasoning=str(data['reasoning'])
            )

        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None

    def classify_product(self, product: Dict[str, Any]) -> ClassificationResult:
        """Classify a single product using rules + LLM fallback.

        Args:
            product: Product dictionary

        Returns:
            ClassificationResult
        """
        # First try simple rules
        rule_result = self.apply_simple_rules(product)

        if rule_result and 'animal' in rule_result and 'label' in rule_result:
            # Both animal and label found with rules
            return ClassificationResult(
                animal=rule_result['animal'],
                label=rule_result['label'],
                confidence=0.9,
                reasoning="Classified using regex rules"
            )

        # Partial or no rule match - would use LLM here
        # For now, return what we found from rules with unknown defaults
        animal = rule_result.get('animal', 'unknown') if rule_result else 'unknown'
        label = rule_result.get('label', 'unknown') if rule_result else 'unknown'

        return ClassificationResult(
            animal=animal,
            label=label,
            confidence=0.7 if rule_result else 0.1,
            reasoning="Partial classification using regex rules (LLM integration needed for full classification)"
        )

    def classify_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify multiple products and add classification results.

        Args:
            products: List of product dictionaries

        Returns:
            List of products with added classification fields
        """
        print(f"Classifying {len(products)} meat products...")

        classified_products = []
        stats = {'rule_classified': 0, 'partial_classified': 0, 'unknown': 0}

        for product in products:
            result = self.classify_product(product)

            # Add classification to product
            classified_product = product.copy()
            classified_product.update({
                'classified_animal': result.animal,
                'classified_label': result.label,
                'classification_confidence': result.confidence,
                'classification_reasoning': result.reasoning
            })

            classified_products.append(classified_product)

            # Update stats
            if result.confidence > 0.8:
                stats['rule_classified'] += 1
            elif result.confidence > 0.5:
                stats['partial_classified'] += 1
            else:
                stats['unknown'] += 1

        print(f"Classification complete:")
        print(f"  Rule-classified: {stats['rule_classified']}")
        print(f"  Partial: {stats['partial_classified']}")
        print(f"  Unknown: {stats['unknown']}")

        return classified_products