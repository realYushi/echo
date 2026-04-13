from __future__ import annotations

from app.schemas.product import Product

SEED_PRODUCTS: list[Product] = [
    # ── Furniture ──────────────────────────────────────────────
    Product(
        id="furniture-001",
        name="Nordic Haven Sofa",
        category="furniture",
        subcategory="sofa",
        tags=["scandinavian", "minimalist", "oak", "linen", "living-room"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Nordic+Haven+Sofa",
        description=(
            "Scandinavian minimalist three-seat sofa crafted from solid white oak with natural linen cushions. "
            "Clean geometric lines and tapered legs create an airy silhouette that anchors any modern living room."
        ),
    ),
    Product(
        id="furniture-002",
        name="Artisan Live-Edge Dining Table",
        category="furniture",
        subcategory="dining-table",
        tags=["rustic", "live-edge", "walnut", "industrial", "dining-room"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Live+Edge+Dining+Table",
        description=(
            "Handcrafted live-edge black walnut dining table on a blackened steel trestle base. "
            "Each slab is unique with natural grain patterns, seating six to eight guests in organic elegance."
        ),
    ),
    Product(
        id="furniture-003",
        name="Modular Wall Bookshelf",
        category="furniture",
        subcategory="bookshelf",
        tags=["modern", "modular", "oak", "storage", "living-room"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Modular+Bookshelf",
        description=(
            "Modular open-frame bookshelf system in natural oak with powder-coated steel brackets. "
            "Configurable grid of cubes and shelves adapts to any wall, blending storage with display."
        ),
    ),
    Product(
        id="furniture-004",
        name="Velvet Swivel Accent Chair",
        category="furniture",
        subcategory="accent-chair",
        tags=["mid-century", "velvet", "swivel", "living-room", "bold"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Velvet+Accent+Chair",
        description=(
            "Mid-century inspired swivel accent chair upholstered in deep emerald velvet with a brushed brass base. "
            "Curved barrel back and plush seat cushion deliver statement comfort for reading nooks or living areas."
        ),
    ),
    Product(
        id="furniture-005",
        name="Concrete & Glass Coffee Table",
        category="furniture",
        subcategory="coffee-table",
        tags=["industrial", "concrete", "glass", "minimalist", "living-room"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Concrete+Coffee+Table",
        description=(
            "Industrial coffee table featuring a micro-concrete base with a tempered glass top. "
            "Raw texture meets transparency for a bold centrepiece that grounds contemporary interiors."
        ),
    ),
    # ── Bathroom ───────────────────────────────────────────────
    Product(
        id="bathroom-001",
        name="Floating Vanity Cabinet",
        category="bathroom",
        subcategory="vanity",
        tags=["modern", "floating", "matte-white", "soft-close", "bathroom"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Floating+Vanity",
        description=(
            "Wall-mounted floating vanity in matte white lacquer with integrated quartz countertop "
            "and undermount basin. "
            "Soft-close drawers and concealed hardware keep the bathroom feeling clean and uncluttered."
        ),
    ),
    Product(
        id="bathroom-002",
        name="Rainfall Shower System",
        category="bathroom",
        subcategory="rain-shower",
        tags=["luxury", "rainfall", "brushed-nickel", "spa", "bathroom"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Rain+Shower+System",
        description=(
            "Thermostatic rainfall shower system with a 12-inch square head in brushed nickel and handheld wand. "
            "Delivers a spa-grade drenching experience with precise temperature control and anti-scald safety valve."
        ),
    ),
    Product(
        id="bathroom-003",
        name="Sculptural Freestanding Bathtub",
        category="bathroom",
        subcategory="freestanding-tub",
        tags=["sculptural", "freestanding", "matte-stone", "spa", "bathroom"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Freestanding+Bathtub",
        description=(
            "Organic sculptural freestanding bathtub in solid-surface matte stone with a thin rolled rim. "
            "Ergonomic lumbar support and deep soaking depth turn the bathroom into a private retreat."
        ),
    ),
    Product(
        id="bathroom-004",
        name="Heated Towel Rack",
        category="bathroom",
        subcategory="towel-rack",
        tags=["heated", "stainless-steel", "wall-mounted", "bathroom", "comfort"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Heated+Towel+Rack",
        description=(
            "Wall-mounted heated towel rack in polished stainless steel with a programmable timer. "
            "Warms towels and robes evenly while doubling as a sleek radiator for smaller bathrooms."
        ),
    ),
    Product(
        id="bathroom-005",
        name="Backlit LED Vanity Mirror",
        category="bathroom",
        subcategory="mirror",
        tags=["led", "backlit", "frameless", "anti-fog", "bathroom"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=LED+Vanity+Mirror",
        description=(
            "Frameless rectangular vanity mirror with perimeter LED backlighting and built-in anti-fog heater. "
            "Touch-dimming and colour-temperature adjustment create perfect grooming light at any hour."
        ),
    ),
    # ── Kitchen ────────────────────────────────────────────────
    Product(
        id="kitchen-001",
        name="Chimney Range Hood",
        category="kitchen",
        subcategory="range-hood",
        tags=["chimney", "stainless-steel", "professional", "ventilation", "kitchen"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Chimney+Range+Hood",
        description=(
            "Professional-grade chimney range hood in brushed stainless steel with 900 CFM blower "
            "and LED task lighting. "
            "Baffle filters and whisper-quiet motor keep the open kitchen clear of smoke and odours."
        ),
    ),
    Product(
        id="kitchen-002",
        name="Pull-Down Kitchen Faucet",
        category="kitchen",
        subcategory="faucet",
        tags=["pull-down", "matte-black", "single-handle", "kitchen", "modern"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Kitchen+Faucet",
        description=(
            "Single-handle pull-down kitchen faucet in matte black with magnetic docking spray head. "
            "Ceramic disc valve and spot-resistant finish ensure years of drip-free, low-maintenance use."
        ),
    ),
    Product(
        id="kitchen-003",
        name="Quartzite Island Countertop",
        category="kitchen",
        subcategory="island-countertop",
        tags=["quartzite", "natural-stone", "island", "premium", "kitchen"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Quartzite+Countertop",
        description=(
            "Polished Taj Mahal quartzite island countertop with soft gold veining on a warm white ground. "
            "Heat-resistant natural stone that serves as the visual and functional heart of a luxury kitchen."
        ),
    ),
    Product(
        id="kitchen-004",
        name="Cluster Pendant Lights",
        category="kitchen",
        subcategory="pendant-lights",
        tags=["pendant", "cluster", "brass", "glass", "kitchen"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Cluster+Pendants",
        description=(
            "Three-piece cluster pendant light set with hand-blown smoked glass globes on slim brass stems. "
            "Staggered drop heights create dynamic overhead illumination above a kitchen island or bar."
        ),
    ),
    Product(
        id="kitchen-005",
        name="Leather-Wrapped Cabinet Handles",
        category="kitchen",
        subcategory="cabinet-handles",
        tags=["leather", "handles", "hardware", "tactile", "kitchen"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Cabinet+Handles",
        description=(
            "Set of ten saddle-stitched vegetable-tanned leather cabinet pulls on solid brass posts. "
            "Warm tactile detail that ages gracefully, adding artisanal character to kitchen cabinetry."
        ),
    ),
    # ── Lighting ───────────────────────────────────────────────
    Product(
        id="lighting-001",
        name="Cascading Crystal Chandelier",
        category="lighting",
        subcategory="chandelier",
        tags=["crystal", "cascading", "luxury", "dining-room", "lighting"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Crystal+Chandelier",
        description=(
            "Multi-tier cascading chandelier with hand-cut crystal prisms on a polished chrome armature. "
            "Throws prismatic light across dining rooms and double-height foyers for dramatic sparkle."
        ),
    ),
    Product(
        id="lighting-002",
        name="Arc Floor Lamp",
        category="lighting",
        subcategory="floor-lamp",
        tags=["arc", "marble-base", "brass", "living-room", "lighting"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Arc+Floor+Lamp",
        description=(
            "Sweeping arc floor lamp with a weighted Carrara marble base and adjustable brushed brass arm. "
            "Linen drum shade softens the light, reaching over sofas and reading chairs without a side table."
        ),
    ),
    Product(
        id="lighting-003",
        name="Geometric Wall Sconce",
        category="lighting",
        subcategory="wall-sconce",
        tags=["geometric", "brass", "ambient", "hallway", "lighting"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Wall+Sconce",
        description=(
            "Angular geometric wall sconce in antique brass with frosted glass panels casting warm uplighting. "
            "Art-deco influenced silhouette adds sculptural interest to hallways and bedrooms."
        ),
    ),
    Product(
        id="lighting-004",
        name="Adjustable LED Track Lighting",
        category="lighting",
        subcategory="track-lighting",
        tags=["led", "track", "adjustable", "gallery", "lighting"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Track+Lighting",
        description=(
            "Low-profile adjustable LED track lighting system with six individually aimable heads in matte white. "
            "Gallery-style directional spots highlight artwork, shelving, and architectural features."
        ),
    ),
    Product(
        id="lighting-005",
        name="Handblown Glass Table Lamp",
        category="lighting",
        subcategory="table-lamp",
        tags=["handblown", "glass", "artisan", "bedroom", "lighting"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Glass+Table+Lamp",
        description=(
            "Artisan handblown glass table lamp in smoky amber with a natural linen shade. "
            "Organic air-bubble inclusions make each piece one-of-a-kind, ideal for bedside or console display."
        ),
    ),
    # ── Building Materials ─────────────────────────────────────
    Product(
        id="materials-001",
        name="Wide-Plank Engineered Hardwood",
        category="building-materials",
        subcategory="hardwood-flooring",
        tags=["hardwood", "wide-plank", "oak", "flooring", "natural"],
        budget_tier="premium",
        image_url="https://placehold.co/400x400?text=Hardwood+Flooring",
        description=(
            "European white oak engineered hardwood in 7-inch wide planks with a matte wire-brushed finish. "
            "Four-layer construction ensures dimensional stability with the warmth and beauty of real wood flooring."
        ),
    ),
    Product(
        id="materials-002",
        name="Zellige Stone Tiles",
        category="building-materials",
        subcategory="stone-tiles",
        tags=["zellige", "terracotta", "handmade", "moroccan", "tiles"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Zellige+Tiles",
        description=(
            "Handmade Moroccan zellige tiles in weathered terracotta with subtle colour variation and irregular edges. "
            "Glazed surface reflects light softly, adding artisanal texture to kitchen backsplashes and shower walls."
        ),
    ),
    Product(
        id="materials-003",
        name="Fluted Glass Partition",
        category="building-materials",
        subcategory="glass-partition",
        tags=["fluted", "glass", "partition", "privacy", "modern"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Glass+Partition",
        description=(
            "Fluted reeded glass partition panel in a slim black steel frame for room division without darkness. "
            "Vertical ribs obscure direct sight lines while transmitting natural light between zones."
        ),
    ),
    Product(
        id="materials-004",
        name="Cast Concrete Wall Panel",
        category="building-materials",
        subcategory="concrete-panel",
        tags=["concrete", "panel", "textured", "industrial", "wall"],
        budget_tier="budget",
        image_url="https://placehold.co/400x400?text=Concrete+Panel",
        description=(
            "Ultra-lightweight cast concrete wall panel with raw board-formed texture for interior accent walls. "
            "Easy clip-mount installation brings brutalist materiality "
            "without the structural weight of poured concrete."
        ),
    ),
    Product(
        id="materials-005",
        name="Blackened Steel Railing",
        category="building-materials",
        subcategory="metal-railing",
        tags=["steel", "blackened", "railing", "staircase", "industrial"],
        budget_tier="mid",
        image_url="https://placehold.co/400x400?text=Steel+Railing",
        description=(
            "Hot-rolled blackened steel staircase railing with flat-bar balusters and a smooth rectangular handrail. "
            "Wax-sealed patina finish adds depth and character while protecting against rust in indoor environments."
        ),
    ),
]
