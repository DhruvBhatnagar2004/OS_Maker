import os
import json
import requests
from pathlib import Path
from django.http import FileResponse, HttpResponse
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.urls import reverse
from .models import OSConfiguration
from .serializers import OSConfigurationSerializer
from .services import ConfigurationService

# Define the base directory
BASE_DIR = Path(settings.BASE_DIR)
PREDEFINED_ISO_PATH = BASE_DIR / "project" / "iso" / "iso.txt"

def serve_iso_file(iso_path):
    """Helper function to serve ISO file"""
    try:
        iso_path_str = str(iso_path.resolve())
        print(f"Attempting to serve ISO from: {iso_path_str}")
        print(f"File exists: {iso_path.exists()}")
        print(f"Is file: {iso_path.is_file()}")

        if iso_path.exists() and iso_path.is_file():
            return FileResponse(
                open(iso_path, 'rb'),
                as_attachment=True,
                filename=iso_path.name
            )
        else:
            print(f"ISO file not found at: {iso_path_str}")
            return None
    except Exception as e:
        print(f"Error serving ISO file: {str(e)}")
        return None

@api_view(['POST'])
def submit_configuration(request):
    try:
        # Parse incoming data and get wallpaper if present
        wallpaper = None
        if request.content_type.startswith('multipart/form-data'):
            config_data = json.loads(request.data.get('config'))
            wallpaper = request.FILES.get('wallpaper')
        else:
            config_data = request.data

        # Extract configuration details
        os_type = config_data.get('operating_system')
        config_type = config_data.get('config_type')
        configuration = config_data.get('configuration', {})

        print(f"Received config_data: {config_data}")

        # Handle Predefined configuration differently
        if config_type == 'Predefined':
            predefined_type = configuration.get('type', '').lower()
            print(f"Processing predefined configuration type: {predefined_type}")

            # Map predefined types to ISO filenames
            iso_filename_map = {
                'minimal': 'minimal.iso',
                'standard': 'standard.iso',
                'workstation': 'full.iso',  # for Ubuntu
                'full': 'full.iso',
                'base': 'base.iso',         # for Arch
                'desktop': 'desktop.iso',
                'gaming': 'gaming.iso'
            }

            # Get distro name in lowercase
            distro = os_type.lower()
            
            # Get corresponding ISO filename
            iso_filename = iso_filename_map.get(predefined_type.lower())
            if not iso_filename:
                return Response(
                    {'error': f'Invalid predefined configuration type: {predefined_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Direct download URL for predefined ISOs
            download_iso_url = f"http://{settings.FLASK_SERVER_IP}:{settings.FLASK_SERVER_PORT}/download-iso/predefined/{distro}/{iso_filename}"
            
            response_data = {
                'operating_system': os_type,
                'config_type': config_type,
                'configuration': {
                    'type': predefined_type
                },
                'download_iso_url': download_iso_url
            }
            
            print(f"Sending predefined response: {response_data}")
            return Response(response_data, status=status.HTTP_201_CREATED)

        # Handle Custom configuration
        # Handle wallpaper upload if present
        if wallpaper:
            print(f"Wallpaper received: {wallpaper.name}")
            
            # Create wallpaper directory if it doesn't exist
            wallpaper_dir = BASE_DIR.parent / "project" / "wallpaper"
            wallpaper_dir.mkdir(parents=True, exist_ok=True)
            
            # Save wallpaper locally
            wallpaper_path = wallpaper_dir / wallpaper.name
            with open(wallpaper_path, 'wb') as f:
                for chunk in wallpaper.chunks():
                    f.write(chunk)
            print(f"Wallpaper written to {wallpaper_path}")

            # Upload to Flask server
            flask_upload_wallpaper = f"http://{settings.FLASK_SERVER_IP}:{settings.FLASK_SERVER_PORT}/upload-wallpaper"
            with open(wallpaper_path, 'rb') as f:
                files = {'file': f}
                upload_wallpaper_response = requests.post(flask_upload_wallpaper, files=files)

            if upload_wallpaper_response.status_code != 200:
                return Response(
                    {'error': 'Failed to upload wallpaper to Flask server'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            print("Wallpaper uploaded to Flask server successfully.")
            
            # Update config data with wallpaper path
            config_data['configuration']['wallpaper_path'] = str(wallpaper_path)
        else:
            print("No wallpaper")
            config_data = request.data
            wallpaper = None

        # Extract configuration details
        os_type = config_data.get('operating_system')
        config_type = config_data.get('config_type')
        configuration = config_data.get('configuration', {})

        # Process packages based on configuration type
        if config_type == 'Predefined':
            packages = ConfigurationService.predefined_service(
                os_type, 
                configuration.get('type')
            )
        else:
            packages = ConfigurationService.customized_service(
                configuration.get('packages', [])
            )

        # Convert packages list to string (one package per line)
        packages_str = '\n'.join(packages)

        # Define the path for packages.txt
        packages_file_path = BASE_DIR.parent / "project" / "packages.txt"

        # Write the packages to packages.txt
        with open(packages_file_path, 'w') as f:
            f.write(packages_str)
        print(f"Packages written to {packages_file_path}")

        # Upload packages.txt to Flask server
        flask_upload_url = f"http://{settings.FLASK_SERVER_IP}:{settings.FLASK_SERVER_PORT}/upload-package"
        with open(packages_file_path, 'rb') as f:
            files = {'file': f}
            upload_response = requests.post(flask_upload_url, files=files)

        if upload_response.status_code != 200:
            return Response(
                {'error': 'Failed to upload packages to Flask server'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        print("Packages uploaded to Flask server successfully.")

        # Determine ISO generation endpoint and set filename with .iso extension
        if os_type.lower() == 'ubuntu':
            generate_iso_endpoint = 'ubuntu'
            default_output_name = 'custom-ubuntu'
        elif os_type.lower() == 'arch':
            generate_iso_endpoint = 'arch'
            default_output_name = 'custom-arch'
        else:
            return Response(
                {'error': 'Unsupported operating system for ISO generation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Construct the Flask ISO generation URL
        generate_iso_url = f"http://{settings.FLASK_SERVER_IP}:{settings.FLASK_SERVER_PORT}/generate-iso/{generate_iso_endpoint}"

        payload = {
            'output_name': default_output_name,
            'wallpaper_path': config_data.get('wallpaper_path')  # Ensure this path is valid on the Flask server
        }

        # Send request to Flask server to generate ISO
        iso_response = requests.post(generate_iso_url, json=payload)

        if iso_response.status_code != 200:
            error_msg = iso_response.json().get('error', 'Unknown error during ISO generation')
            return Response(
                {'error': f"Failed to generate ISO: {error_msg}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        iso_message = iso_response.json().get('message', '')
        print(f"ISO Generation Response: {iso_message}")

        # Prepare data for saving in the database
        save_data = {
            'operating_system': os_type,
            'config_type': config_type,
            'configuration_type': configuration.get('type'),
            'packages': packages,
            'has_custom_wallpaper': configuration.get('has_custom_wallpaper', False)
        }


        serializer = OSConfigurationSerializer(data=save_data)
        if serializer.is_valid():
            print("in fi")
            instance = serializer.save()
            print("before`")
            
            download_iso_url = f"http://{settings.FLASK_SERVER_IP}:{settings.FLASK_SERVER_PORT}/download-iso/{generate_iso_endpoint}/{default_output_name}.iso"
            print("after")
            response_data = {
                'operating_system': os_type,
                'config_type': config_type,
                'configuration': {
                    'type': configuration.get('type'),
                    'packages': packages,
                    'has_custom_wallpaper': configuration.get('has_custom_wallpaper', False)
                },
                'iso_generation': "iso_message",
                'download_iso_url': download_iso_url  # Direct link to Flask's download endpoint
            }
            print(response_data)

            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            print("not valid")
            print(serializer.errors)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Exception in submit_configuration: {str(e)}")
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def download_iso(request, config_id):
    """Endpoint to download ISO file for a given configuration."""
    try:
        configuration = OSConfiguration.objects.get(id=config_id)
        if configuration.config_type != 'Predefined':
            return Response(
                {'error': 'ISO download is only available for Predefined configurations.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        iso_response = serve_iso_file(PREDEFINED_ISO_PATH)
        if iso_response:
            return iso_response
        else:
            return Response(
                {'error': 'ISO file not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    except OSConfiguration.DoesNotExist:
        return Response(
            {'error': 'Configuration not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"Error in download_iso: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def home_view(request):
    return Response({
        'message': 'Welcome to OS Maker API',
        'endpoints': {
            'configurations': '/api/configurations/submit'
        }
    })

# Create your views here.
