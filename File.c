#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <direct.h>
#include <sys/stat.h>
#include <windows.h>

#define AUTHOR_NAME "MD. Naiem Islam Nahid"
#define BASE_DIR "generated_folders"

// Function to generate random string
void generate_random_word(char *word, int length) {
    const char charset[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    int charset_length = strlen(charset);
    
    for (int i = 0; i < length; i++) {
        int index = rand() % charset_length;
        word[i] = charset[index];
    }
    word[length] = '\0';
}

// Function to get current timestamp with nanoseconds
void get_timestamp(char *timestamp) {
    SYSTEMTIME st;
    GetLocalTime(&st);
    
    sprintf(timestamp, "%04d-%02d-%02d_%02d-%02d-%02d-%03d",
            st.wYear, st.wMonth, st.wDay,
            st.wHour, st.wMinute, st.wSecond,
            st.wMilliseconds);
}

// Function to generate UUID-like string
void generate_uuid(char *uuid) {
    const char charset[] = "0123456789abcdef";
    const char* uuid_template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx";
    int i;
    
    for (i = 0; uuid_template[i] != '\0'; i++) {
        if (uuid_template[i] == 'x') {
            uuid[i] = charset[rand() % 16];
        } else if (uuid_template[i] == 'y') {
            uuid[i] = charset[(rand() & 0x3) | 0x8];
        } else {
            uuid[i] = uuid_template[i];
        }
    }
    uuid[i] = '\0';
}

// Function to execute git command
void git_commit(const char *message) {
    char command[1024];
    snprintf(command, sizeof(command), "git add . && git commit -m \"%s\" --quiet", message);
    system(command);
}

int main() {
    srand((unsigned int)time(NULL));
    
    // Create base directory
    _mkdir(BASE_DIR);
    
    printf("Starting folder generation process...\n");
    
    // Create 1000 folders
    for (int folder_num = 1; folder_num <= 1000; folder_num++) {
        char random_word[9];
        generate_random_word(random_word, 8);
        
        char folder_name[100];
        snprintf(folder_name, sizeof(folder_name), "%s/%04d_%s", BASE_DIR, folder_num, random_word);
        
        // Create folder
        _mkdir(folder_name);
        
        // Git commit for folder creation
        char commit_msg[200];
        snprintf(commit_msg, sizeof(commit_msg), "Created folder: %04d_%s", folder_num, random_word);
        git_commit(commit_msg);
        
        // Create 100 files in the folder
        for (int file_num = 1; file_num <= 100; file_num++) {
            char timestamp[50];
            get_timestamp(timestamp);
            
            char uuid[37];
            generate_uuid(uuid);
            
            char file_path[256];
            snprintf(file_path, sizeof(file_path), "%s/%04d_%s_%s.txt", 
                    folder_name, folder_num, random_word, timestamp);
            
            // Create and write to file
            FILE *file = fopen(file_path, "w");
            if (file != NULL) {
                fprintf(file, "Timestamp: %s\n", timestamp);
                fprintf(file, "Date: %.10s\n", timestamp);
                fprintf(file, "Created by: %s\n", AUTHOR_NAME);
                fprintf(file, "Folder: %04d_%s\n", folder_num, random_word);
                fprintf(file, "File: %04d_%s_%s.txt\n", folder_num, random_word, timestamp);
                fprintf(file, "UUID: %s\n", uuid);
                fclose(file);
                
                // Git commit for file creation
                snprintf(commit_msg, sizeof(commit_msg), 
                        "Created file in %04d_%s: %04d_%s_%s.txt",
                        folder_num, random_word, folder_num, random_word, timestamp);
                git_commit(commit_msg);
            }
        }
        
        printf("Completed folder %d/1000: %04d_%s\n", 
               folder_num, folder_num, random_word);
    }
    
    printf("Successfully created all folders and files with git commits!\n");
    return 0;
}