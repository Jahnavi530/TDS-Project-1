import requests
import csv
import time
import os

GITHUB_TOKEN = " tds-project-token-1"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def get_users_in_city(city="Toronto", min_followers=100):
    users = []
    query = f"location:{city}+followers:>{min_followers}"
    page = 1
    per_page = 100
    total_users = 0

    while True:
        url = f"https://api.github.com/search/users?q={query}&per_page={per_page}&page={page}"
        response = requests.get(url, headers=HEADERS)
        print(f"Fetching page {page}...")

        if response.status_code != 200:
            print("Error fetching data:", response.json())
            break

        data = response.json()
        users.extend(data['items'])
        total_users += len(data['items'])

        if len(data['items']) < per_page:
            break

        page += 1
        time.sleep(1)  # Rate limiting

    detailed_users = [get_user_details(user['login']) for user in users]
    return detailed_users

def get_user_details(username):
    user_url = f"https://api.github.com/users/{username}"
    user_data = requests.get(user_url, headers=HEADERS).json()

    return {
        'login': user_data.get('login', ''),
        'name': user_data.get('name', ''),
        'company': clean_company_name(user_data.get('company')),
        'location': user_data.get('location', ''),
        'email': user_data.get('email', ''),
        'hireable': user_data.get('hireable', ''),
        'bio': user_data.get('bio', ''),
        'public_repos': user_data.get('public_repos', 0),
        'followers': user_data.get('followers', 0),
        'following': user_data.get('following', 0),
        'created_at': user_data.get('created_at', ''),
    }

def clean_company_name(company):
    if company:
        company = company.strip().upper()
        if company.startswith('@'):
            company = company[1:]
    return company or ""

def get_user_repos(username):
    repos = []
    page = 1
    per_page = 100
    while True:
        repos_url = f"https://api.github.com/users/{username}/repos?per_page={per_page}&page={page}"
        response = requests.get(repos_url, headers=HEADERS)
        if response.status_code != 200:
            print("Error fetching repos for user:", username)
            break

        repos_data = response.json()
        if not repos_data:
            break

        for repo in repos_data:
            repos.append({
                'login': username,
                'full_name': repo['full_name'],
                'created_at': repo['created_at'],
                'stargazers_count': repo['stargazers_count'],
                'watchers_count': repo['watchers_count'],
                'language': repo.get('language', ''),
                'has_projects': repo.get('has_projects', False),
                'has_wiki': repo.get('has_wiki', False),
                'license_name': repo['license']['key'] if repo.get('license') else '',
            })

        page += 1
        time.sleep(1)  # Rate limiting

    return repos

def save_to_csv(data, filename, fieldnames):
    os.makedirs("output", exist_ok=True)
    filepath = os.path.join("output", filename)
    with open(filepath, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    users = get_users_in_city("Toronto", 100)
    save_to_csv(users, 'users.csv', [
        'login', 'name', 'company', 'location', 'email', 'hireable', 'bio', 
        'public_repos', 'followers', 'following', 'created_at'
    ])

    all_repos = []
    for user in users:
        repos = get_user_repos(user['login'])
        all_repos.extend(repos)

    save_to_csv(all_repos, 'repositories.csv', [
        'login', 'full_name', 'created_at', 'stargazers_count', 'watchers_count', 
        'language', 'has_projects', 'has_wiki', 'license_name'
    ])
    print("Data saved successfully!")

