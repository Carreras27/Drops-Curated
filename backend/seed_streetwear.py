import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

# All Indian Streetwear Brand Products
STREETWEAR_PRODUCTS = [
    # VEG NON VEG
    {'id': 'sw_001', 'name': 'VNV OG Hoodie Black', 'slug': 'vnv-og-hoodie-black', 'brand': 'Veg Non Veg', 'category': 'CLOTHES', 'description': 'Premium heavyweight hoodie with signature VNV branding', 'imageUrl': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500', 'tags': ['hoodie', 'streetwear', 'indian', 'vegnon veg', 'oversized'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    {'id': 'sw_002', 'name': 'VNV Graphic Tee White', 'slug': 'vnv-graphic-tee', 'brand': 'Veg Non Veg', 'category': 'CLOTHES', 'description': 'Limited edition graphic tee', 'imageUrl': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500', 'tags': ['tshirt', 'streetwear', 'limited-edition', 'graphic'], 'priceRange': 'BUDGET', 'isActive': True, 'isTrending': False},
    
    # BLU ORANGE
    {'id': 'sw_003', 'name': 'Blu Orange Cargo Pants', 'slug': 'blu-orange-cargo', 'brand': 'Blu Orange', 'category': 'CLOTHES', 'description': 'Technical cargo pants with multiple pockets', 'imageUrl': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500', 'tags': ['cargo', 'pants', 'streetwear', 'utility'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    {'id': 'sw_004', 'name': 'Blu Orange Oversized Shirt', 'slug': 'blu-orange-shirt', 'brand': 'Blu Orange', 'category': 'CLOTHES', 'description': 'Relaxed fit oversized shirt', 'imageUrl': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500', 'tags': ['shirt', 'oversized', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # CREP DOG CREW
    {'id': 'sw_005', 'name': 'Crep Dog Crew High Top Sneakers', 'slug': 'cdc-high-top', 'brand': 'Crep Dog Crew', 'category': 'SHOES', 'description': 'Premium high-top sneakers with CDC branding', 'imageUrl': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500', 'tags': ['sneakers', 'high-top', 'streetwear', 'shoes', 'footwear'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': True},
    {'id': 'sw_006', 'name': 'Crep Dog Crew Low Top White', 'slug': 'cdc-low-top', 'brand': 'Crep Dog Crew', 'category': 'SHOES', 'description': 'Clean white low-top sneakers', 'imageUrl': 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=500', 'tags': ['sneakers', 'low-top', 'white', 'shoes'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': True},
    
    # SUPER KICKS
    {'id': 'sw_007', 'name': 'Super Kicks Classic White', 'slug': 'superkicks-classic-white', 'brand': 'Super Kicks', 'category': 'SHOES', 'description': 'Iconic white sneakers from Indian brand', 'imageUrl': 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500', 'tags': ['sneakers', 'classic', 'white', 'shoes', 'footwear'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': True},
    {'id': 'sw_008', 'name': 'Super Kicks Jordan Style', 'slug': 'superkicks-jordan', 'brand': 'Super Kicks', 'category': 'SHOES', 'description': 'Basketball-inspired high tops', 'imageUrl': 'https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?w=500', 'tags': ['sneakers', 'basketball', 'high-top', 'shoes'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': True},
    
    # CULTURE CIRCLE
    {'id': 'sw_009', 'name': 'Culture Circle Utility Cargo', 'slug': 'cc-utility-cargo', 'brand': 'Culture Circle', 'category': 'CLOTHES', 'description': 'Multi-pocket utility cargo pants', 'imageUrl': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500', 'tags': ['cargo', 'utility', 'streetwear', 'pants'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    {'id': 'sw_010', 'name': 'Culture Circle Logo Hoodie', 'slug': 'cc-logo-hoodie', 'brand': 'Culture Circle', 'category': 'CLOTHES', 'description': 'Statement hoodie with bold branding', 'imageUrl': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500', 'tags': ['hoodie', 'logo', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # JAYWALKING
    {'id': 'sw_011', 'name': 'Jaywalking Distressed Denim', 'slug': 'jw-distressed-denim', 'brand': 'Jaywalking', 'category': 'CLOTHES', 'description': 'Ripped and distressed denim jeans', 'imageUrl': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=500', 'tags': ['jeans', 'denim', 'distressed', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    {'id': 'sw_012', 'name': 'Jaywalking Bomber Jacket', 'slug': 'jw-bomber', 'brand': 'Jaywalking', 'category': 'CLOTHES', 'description': 'Classic bomber with streetwear edge', 'imageUrl': 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=500', 'tags': ['jacket', 'bomber', 'streetwear'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': False},
    
    # ALMOST GODS
    {'id': 'sw_013', 'name': 'Almost Gods Graphic Hoodie', 'slug': 'ag-graphic-hoodie', 'brand': 'Almost Gods', 'category': 'CLOTHES', 'description': 'Bold graphic print hoodie', 'imageUrl': 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=500', 'tags': ['hoodie', 'graphic', 'streetwear', 'bold'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    {'id': 'sw_014', 'name': 'Almost Gods Oversized Tee', 'slug': 'ag-oversized-tee', 'brand': 'Almost Gods', 'category': 'CLOTHES', 'description': 'Dropped shoulder oversized fit', 'imageUrl': 'https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=500', 'tags': ['tshirt', 'oversized', 'streetwear'], 'priceRange': 'BUDGET', 'isActive': True, 'isTrending': False},
    
    # DAWN TAWN
    {'id': 'sw_015', 'name': 'Dawn Tawn Minimalist Sneakers', 'slug': 'dt-minimal-sneakers', 'brand': 'Dawn Tawn', 'category': 'SHOES', 'description': 'Clean minimalist design', 'imageUrl': 'https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=500', 'tags': ['sneakers', 'minimalist', 'clean', 'shoes'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # COMET
    {'id': 'sw_016', 'name': 'Comet Tech Joggers', 'slug': 'comet-tech-joggers', 'brand': 'Comet', 'category': 'CLOTHES', 'description': 'Technical fabric joggers', 'imageUrl': 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=500', 'tags': ['joggers', 'technical', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # MIDNIGHT LAW
    {'id': 'sw_017', 'name': 'Midnight Law Black Hoodie', 'slug': 'ml-black-hoodie', 'brand': 'Midnight Law', 'category': 'CLOTHES', 'description': 'All-black premium hoodie', 'imageUrl': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500', 'tags': ['hoodie', 'black', 'dark', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # NOUGHTONE
    {'id': 'sw_018', 'name': 'Noughtone Designer Tee', 'slug': 'noughtone-designer-tee', 'brand': 'Noughtone', 'category': 'CLOTHES', 'description': 'Artist collaboration tee', 'imageUrl': 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=500', 'tags': ['tshirt', 'designer', 'collab', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # DRIPPINN MONCKY
    {'id': 'sw_019', 'name': 'Drippinn Moncky Sweatpants', 'slug': 'dm-sweatpants', 'brand': 'Drippinn Moncky', 'category': 'CLOTHES', 'description': 'Comfort fit sweatpants', 'imageUrl': 'https://images.unsplash.com/photo-1517438476312-10d79c077509?w=500', 'tags': ['sweatpants', 'comfort', 'streetwear'], 'priceRange': 'BUDGET', 'isActive': True, 'isTrending': False},
    
    # SMOKELAB
    {'id': 'sw_020', 'name': 'Smokelab Grunge Tee', 'slug': 'smokelab-grunge-tee', 'brand': 'Smokelab', 'category': 'CLOTHES', 'description': 'Vintage grunge aesthetic tee', 'imageUrl': 'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=500', 'tags': ['tshirt', 'grunge', 'vintage', 'streetwear'], 'priceRange': 'BUDGET', 'isActive': True, 'isTrending': False},
    
    # SHIARAI
    {'id': 'sw_021', 'name': 'Shiarai Japanese Inspired Jacket', 'slug': 'shiarai-jacket', 'brand': 'Shiarai', 'category': 'CLOTHES', 'description': 'Japanese aesthetic street jacket', 'imageUrl': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=500', 'tags': ['jacket', 'japanese', 'anime', 'streetwear'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': True},
    
    # EXHALE
    {'id': 'sw_022', 'name': 'Exhale Relaxed Fit Hoodie', 'slug': 'exhale-relaxed-hoodie', 'brand': 'Exhale', 'category': 'CLOTHES', 'description': 'Comfort-first relaxed hoodie', 'imageUrl': 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=500', 'tags': ['hoodie', 'relaxed', 'comfort', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    {'id': 'sw_023', 'name': 'Exhale Wide Leg Pants', 'slug': 'exhale-wide-leg', 'brand': 'Exhale', 'category': 'CLOTHES', 'description': 'Trendy wide leg pants', 'imageUrl': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500', 'tags': ['pants', 'wide-leg', 'trendy', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    
    # TOFFLE
    {'id': 'sw_024', 'name': 'Toffle Retro Sneakers', 'slug': 'toffle-retro-sneakers', 'brand': 'Toffle', 'category': 'SHOES', 'description': '90s inspired retro sneakers', 'imageUrl': 'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=500', 'tags': ['sneakers', 'retro', '90s', 'shoes', 'footwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    
    # BISKIT
    {'id': 'sw_025', 'name': 'Biskit Patchwork Denim', 'slug': 'biskit-patchwork-denim', 'brand': 'Biskit', 'category': 'CLOTHES', 'description': 'Unique patchwork denim jeans', 'imageUrl': 'https://images.unsplash.com/photo-1475178626620-a4d074967452?w=500', 'tags': ['jeans', 'denim', 'patchwork', 'unique'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': False},
    
    # FKNS
    {'id': 'sw_026', 'name': 'FKNS Statement Hoodie', 'slug': 'fkns-statement-hoodie', 'brand': 'FKNS', 'category': 'CLOTHES', 'description': 'Bold statement hoodie', 'imageUrl': 'https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=500', 'tags': ['hoodie', 'statement', 'bold', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    
    # NARENDRA KUMAR
    {'id': 'sw_027', 'name': 'Narendra Kumar Designer Jacket', 'slug': 'nk-designer-jacket', 'brand': 'Narendra Kumar', 'category': 'CLOTHES', 'description': 'High-fashion street jacket', 'imageUrl': 'https://images.unsplash.com/photo-1495105787522-5334e3ffa0ef?w=500', 'tags': ['jacket', 'designer', 'high-fashion', 'streetwear'], 'priceRange': 'LUXURY', 'isActive': True, 'isTrending': False},
    
    # ASK BY AVISHI
    {'id': 'sw_028', 'name': 'Ask by Avishi Crop Top', 'slug': 'aba-crop-top', 'brand': 'Ask by Avishi', 'category': 'CLOTHES', 'description': 'Trendy crop top for women', 'imageUrl': 'https://images.unsplash.com/photo-1562137369-1a1a0bc66744?w=500', 'tags': ['crop-top', 'women', 'trendy', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    {'id': 'sw_029', 'name': 'Ask by Avishi Baggy Jeans', 'slug': 'aba-baggy-jeans', 'brand': 'Ask by Avishi', 'category': 'CLOTHES', 'description': 'Y2K style baggy jeans', 'imageUrl': 'https://images.unsplash.com/photo-1582418702059-97ebafb35d09?w=500', 'tags': ['jeans', 'baggy', 'y2k', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': True},
    
    # NOUGHTONE (More products)
    {'id': 'sw_030', 'name': 'Noughtone Minimal Sneakers', 'slug': 'noughtone-minimal', 'brand': 'Noughtone', 'category': 'SHOES', 'description': 'Minimalist white sneakers', 'imageUrl': 'https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=500', 'tags': ['sneakers', 'minimalist', 'white', 'shoes'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # SMOKELAB (More)
    {'id': 'sw_031', 'name': 'Smokelab Vintage Wash Hoodie', 'slug': 'smokelab-vintage-hoodie', 'brand': 'Smokelab', 'category': 'CLOTHES', 'description': 'Acid wash vintage hoodie', 'imageUrl': 'https://images.unsplash.com/photo-1620799139834-6b8f844febe6?w=500', 'tags': ['hoodie', 'vintage', 'wash', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
    
    # DRIPPINN MONCKY (More)
    {'id': 'sw_032', 'name': 'Drippinn Moncky Track Pants', 'slug': 'dm-track-pants', 'brand': 'Drippinn Moncky', 'category': 'CLOTHES', 'description': 'Athletic track pants with stripes', 'imageUrl': 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=500', 'tags': ['track-pants', 'athletic', 'streetwear'], 'priceRange': 'BUDGET', 'isActive': True, 'isTrending': False},
    
    # MIDNIGHT LAW (More)
    {'id': 'sw_033', 'name': 'Midnight Law Gothic Tee', 'slug': 'ml-gothic-tee', 'brand': 'Midnight Law', 'category': 'CLOTHES', 'description': 'Dark gothic aesthetic tee', 'imageUrl': 'https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=500', 'tags': ['tshirt', 'gothic', 'dark', 'streetwear'], 'priceRange': 'BUDGET', 'isActive': True, 'isTrending': False},
    
    # SHIARAI (More)
    {'id': 'sw_034', 'name': 'Shiarai Harajuku Pants', 'slug': 'shiarai-harajuku', 'brand': 'Shiarai', 'category': 'CLOTHES', 'description': 'Japanese Harajuku style pants', 'imageUrl': 'https://images.unsplash.com/photo-1624378440070-7b4989c680b3?w=500', 'tags': ['pants', 'harajuku', 'japanese', 'streetwear'], 'priceRange': 'PREMIUM', 'isActive': True, 'isTrending': True},
    
    # COMET (More)
    {'id': 'sw_035', 'name': 'Comet Space Dye Hoodie', 'slug': 'comet-space-dye', 'brand': 'Comet', 'category': 'CLOTHES', 'description': 'Space dye pattern hoodie', 'imageUrl': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500', 'tags': ['hoodie', 'space-dye', 'unique', 'streetwear'], 'priceRange': 'MID_RANGE', 'isActive': True, 'isTrending': False},
]

# Prices for all streetwear products
STREETWEAR_PRICES = [
    {'id': 'swp_001', 'productId': 'sw_001', 'store': 'VEG_NON_VEG', 'productUrl': 'https://vegnonveg.com', 'currentPrice': 3499, 'originalPrice': 4999, 'discountPercent': 30, 'inStock': True},
    {'id': 'swp_002', 'productId': 'sw_002', 'store': 'VEG_NON_VEG', 'productUrl': 'https://vegnonveg.com', 'currentPrice': 1499, 'originalPrice': 1999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_003', 'productId': 'sw_003', 'store': 'BLU_ORANGE', 'productUrl': 'https://bluorange.in', 'currentPrice': 3999, 'originalPrice': 5499, 'discountPercent': 27, 'inStock': True},
    {'id': 'swp_004', 'productId': 'sw_004', 'store': 'BLU_ORANGE', 'productUrl': 'https://bluorange.in', 'currentPrice': 2999, 'originalPrice': 3999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_005', 'productId': 'sw_005', 'store': 'CREP_DOG_CREW', 'productUrl': 'https://crepdogcrew.com', 'currentPrice': 7999, 'originalPrice': 9999, 'discountPercent': 20, 'inStock': True},
    {'id': 'swp_006', 'productId': 'sw_006', 'store': 'CREP_DOG_CREW', 'productUrl': 'https://crepdogcrew.com', 'currentPrice': 6999, 'originalPrice': 8999, 'discountPercent': 22, 'inStock': True},
    {'id': 'swp_007', 'productId': 'sw_007', 'store': 'SUPER_KICKS', 'productUrl': 'https://superkicks.in', 'currentPrice': 5999, 'originalPrice': 7999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_008', 'productId': 'sw_008', 'store': 'SUPER_KICKS', 'productUrl': 'https://superkicks.in', 'currentPrice': 8999, 'originalPrice': 11999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_009', 'productId': 'sw_009', 'store': 'CULTURE_CIRCLE', 'productUrl': 'https://culturecircle.in', 'currentPrice': 3499, 'originalPrice': 4999, 'discountPercent': 30, 'inStock': True},
    {'id': 'swp_010', 'productId': 'sw_010', 'store': 'CULTURE_CIRCLE', 'productUrl': 'https://culturecircle.in', 'currentPrice': 2999, 'originalPrice': 3999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_011', 'productId': 'sw_011', 'store': 'JAYWALKING', 'productUrl': 'https://jaywalking.in', 'currentPrice': 3999, 'originalPrice': 5499, 'discountPercent': 27, 'inStock': True},
    {'id': 'swp_012', 'productId': 'sw_012', 'store': 'JAYWALKING', 'productUrl': 'https://jaywalking.in', 'currentPrice': 5999, 'originalPrice': 7999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_013', 'productId': 'sw_013', 'store': 'ALMOST_GODS', 'productUrl': 'https://almostgods.com', 'currentPrice': 3299, 'originalPrice': 4499, 'discountPercent': 27, 'inStock': True},
    {'id': 'swp_014', 'productId': 'sw_014', 'store': 'ALMOST_GODS', 'productUrl': 'https://almostgods.com', 'currentPrice': 1799, 'originalPrice': 2499, 'discountPercent': 28, 'inStock': True},
    {'id': 'swp_015', 'productId': 'sw_015', 'store': 'DAWN_TAWN', 'productUrl': 'https://dawntawn.com', 'currentPrice': 4499, 'originalPrice': 5999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_016', 'productId': 'sw_016', 'store': 'COMET', 'productUrl': 'https://comet.in', 'currentPrice': 2799, 'originalPrice': 3499, 'discountPercent': 20, 'inStock': True},
    {'id': 'swp_017', 'productId': 'sw_017', 'store': 'MIDNIGHT_LAW', 'productUrl': 'https://midnightlaw.in', 'currentPrice': 3199, 'originalPrice': 4299, 'discountPercent': 26, 'inStock': True},
    {'id': 'swp_018', 'productId': 'sw_018', 'store': 'NOUGHTONE', 'productUrl': 'https://noughtone.com', 'currentPrice': 2499, 'originalPrice': 3299, 'discountPercent': 24, 'inStock': True},
    {'id': 'swp_019', 'productId': 'sw_019', 'store': 'DRIPPINN_MONCKY', 'productUrl': 'https://drippinnmoncky.com', 'currentPrice': 2299, 'originalPrice': 2999, 'discountPercent': 23, 'inStock': True},
    {'id': 'swp_020', 'productId': 'sw_020', 'store': 'SMOKELAB', 'productUrl': 'https://smokelab.in', 'currentPrice': 1799, 'originalPrice': 2499, 'discountPercent': 28, 'inStock': True},
    {'id': 'swp_021', 'productId': 'sw_021', 'store': 'SHIARAI', 'productUrl': 'https://shiarai.com', 'currentPrice': 6999, 'originalPrice': 9999, 'discountPercent': 30, 'inStock': True},
    {'id': 'swp_022', 'productId': 'sw_022', 'store': 'EXHALE', 'productUrl': 'https://exhale.in', 'currentPrice': 2999, 'originalPrice': 3999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_023', 'productId': 'sw_023', 'store': 'EXHALE', 'productUrl': 'https://exhale.in', 'currentPrice': 3299, 'originalPrice': 4499, 'discountPercent': 27, 'inStock': True},
    {'id': 'swp_024', 'productId': 'sw_024', 'store': 'TOFFLE', 'productUrl': 'https://toffle.in', 'currentPrice': 4999, 'originalPrice': 6499, 'discountPercent': 23, 'inStock': True},
    {'id': 'swp_025', 'productId': 'sw_025', 'store': 'BISKIT', 'productUrl': 'https://biskit.in', 'currentPrice': 5999, 'originalPrice': 7999, 'discountPercent': 25, 'inStock': True},
    {'id': 'swp_026', 'productId': 'sw_026', 'store': 'FKNS', 'productUrl': 'https://fkns.in', 'currentPrice': 3499, 'originalPrice': 4799, 'discountPercent': 27, 'inStock': True},
    {'id': 'swp_027', 'productId': 'sw_027', 'store': 'NARENDRA_KUMAR', 'productUrl': 'https://narendrakumar.com', 'currentPrice': 12999, 'originalPrice': 16999, 'discountPercent': 24, 'inStock': True},
    {'id': 'swp_028', 'productId': 'sw_028', 'store': 'ASK_BY_AVISHI', 'productUrl': 'https://askbyavishi.com', 'currentPrice': 2499, 'originalPrice': 3299, 'discountPercent': 24, 'inStock': True},
    {'id': 'swp_029', 'productId': 'sw_029', 'store': 'ASK_BY_AVISHI', 'productUrl': 'https://askbyavishi.com', 'currentPrice': 3799, 'originalPrice': 4999, 'discountPercent': 24, 'inStock': True},
    {'id': 'swp_030', 'productId': 'sw_030', 'store': 'NOUGHTONE', 'productUrl': 'https://noughtone.com', 'currentPrice': 4299, 'originalPrice': 5499, 'discountPercent': 22, 'inStock': True},
    {'id': 'swp_031', 'productId': 'sw_031', 'store': 'SMOKELAB', 'productUrl': 'https://smokelab.in', 'currentPrice': 3199, 'originalPrice': 4299, 'discountPercent': 26, 'inStock': True},
    {'id': 'swp_032', 'productId': 'sw_032', 'store': 'DRIPPINN_MONCKY', 'productUrl': 'https://drippinnmoncky.com', 'currentPrice': 2599, 'originalPrice': 3499, 'discountPercent': 26, 'inStock': True},
    {'id': 'swp_033', 'productId': 'sw_033', 'store': 'MIDNIGHT_LAW', 'productUrl': 'https://midnightlaw.in', 'currentPrice': 1899, 'originalPrice': 2499, 'discountPercent': 24, 'inStock': True},
    {'id': 'swp_034', 'productId': 'sw_034', 'store': 'SHIARAI', 'productUrl': 'https://shiarai.com', 'currentPrice': 4999, 'originalPrice': 6999, 'discountPercent': 29, 'inStock': True},
    {'id': 'swp_035', 'productId': 'sw_035', 'store': 'COMET', 'productUrl': 'https://comet.in', 'currentPrice': 3399, 'originalPrice': 4499, 'discountPercent': 24, 'inStock': True},
]

async def seed_streetwear():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'indiashop_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔥 Adding ALL Indian Streetwear Brands...")
    print("=" * 60)
    
    # Add timestamps
    for product in STREETWEAR_PRODUCTS:
        product['createdAt'] = datetime.now(timezone.utc).isoformat()
        product['updatedAt'] = datetime.now(timezone.utc).isoformat()
        product['attributes'] = {'sizes': ['S', 'M', 'L', 'XL'], 'colors': ['Black', 'White']}
        product['additionalImages'] = []
        product['gender'] = 'UNISEX'
    
    for price in STREETWEAR_PRICES:
        price['lastScrapedAt'] = datetime.now(timezone.utc).isoformat()
        price['createdAt'] = datetime.now(timezone.utc).isoformat()
    
    # Insert products
    await db.products.insert_many(STREETWEAR_PRODUCTS)
    print(f"✅ Added {len(STREETWEAR_PRODUCTS)} streetwear products")
    
    # Insert prices
    await db.prices.insert_many(STREETWEAR_PRICES)
    print(f"✅ Added {len(STREETWEAR_PRICES)} prices")
    
    # Show summary
    brands = {}
    for product in STREETWEAR_PRODUCTS:
        brand = product['brand']
        brands[brand] = brands.get(brand, 0) + 1
    
    print(f"\n📊 Brands Added:")
    for brand, count in sorted(brands.items()):
        print(f"  • {brand}: {count} products")
    
    total_products = await db.products.count_documents({})
    total_prices = await db.prices.count_documents({})
    
    print(f"\n🎉 Database Status:")
    print(f"  • Total Products: {total_products}")
    print(f"  • Total Prices: {total_prices}")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_streetwear())
