#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <random>
#include <filesystem>
#include <iomanip>
#include <thread>
#include <sstream>
#include <cstdlib>

namespace fs = std::filesystem;

class FolderGenerator {
private:
    const std::string AUTHOR_NAME = "MD. Naiem Islam Nahid";
    const std::string BASE_DIR = "generated_folders_cpp";
    std::random_device rd;
    std::mt19937 gen;
    std::uniform_int_distribution<> dist_char;

    std::string generateRandomWord(int length = 8) {
        std::string result;
        result.reserve(length);
        static const char charset[] = 
            "0123456789"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz";

        for (int i = 0; i < length; ++i) {
            result += charset[dist_char(gen) % (sizeof(charset) - 1)];
        }
        return result;
    }

    std::string getCurrentTimestamp() {
        auto now = std::chrono::system_clock::now();
        auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            now.time_since_epoch()
        );
        
        auto now_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&now_t), "%Y-%m-%d_%H-%M-%S");
        ss << "-" << std::setfill('0') << std::setw(9) << now_ns.count() % 1000000000;
        return ss.str();
    }

    std::string generateUUID() {
        static std::random_device rd;
        static std::mt19937 gen(rd());
        static std::uniform_int_distribution<> dis(0, 15);
        static const char* digits = "0123456789abcdef";
        
        std::string uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx";
        for (char& c : uuid) {
            if (c == 'x') c = digits[dis(gen)];
            else if (c == 'y') c = digits[(dis(gen) & 0x3) | 0x8];
        }
        return uuid;
    }

    void gitCommit(const std::string& message) {
        std::string cmd = "git add . && git commit -m \"" + message + "\" --quiet";
        system(cmd.c_str());
    }

public:
    FolderGenerator() : gen(rd()), dist_char(0, 61) {
        fs::create_directories(BASE_DIR);
    }

    void generate() {
        std::cout << "Starting folder generation process...\n";
        
        #pragma omp parallel for
        for (int folder_num = 1; folder_num <= 1000; ++folder_num) {
            std::string random_word = generateRandomWord();
            std::string folder_name = std::to_string(folder_num);
            folder_name = std::string(4 - folder_name.length(), '0') + folder_name;
            folder_name += "_" + random_word;

            std::string folder_path = BASE_DIR + "/" + folder_name;
            fs::create_directories(folder_path);

            // Git commit for folder creation
            gitCommit("Created folder: " + folder_name);

            // Create 100 files in parallel
            for (int file_num = 1; file_num <= 100; ++file_num) {
                std::string timestamp = getCurrentTimestamp();
                std::string file_name = folder_name + "_" + timestamp + ".txt";
                std::string file_path = folder_path + "/" + file_name;

                std::ofstream file(file_path);
                if (file.is_open()) {
                    file << "Timestamp: " << timestamp << "\n"
                         << "Date: " << timestamp.substr(0, 10) << "\n"
                         << "Created by: " << AUTHOR_NAME << "\n"
                         << "Folder: " << folder_name << "\n"
                         << "File: " << file_name << "\n"
                         << "UUID: " << generateUUID() << "\n";
                    file.close();

                    // Git commit for file creation
                    gitCommit("Created file in " + folder_name + ": " + file_name);
                }
            }

            std::cout << "Completed folder " << folder_num << "/1000: " << folder_name << "\n";
        }
    }
};

int main() {
    try {
        auto start = std::chrono::high_resolution_clock::now();
        
        FolderGenerator generator;
        generator.generate();
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::seconds>(end - start);
        
        std::cout << "Successfully created all folders and files with git commits!\n";
        std::cout << "Total time taken: " << duration.count() << " seconds\n";
    }
    catch (const std::exception& e) {
        std::cerr << "An error occurred: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}