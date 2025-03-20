#!/usr/bin/python3

# IMPORTS =====================================================================
import re
import os
import argparse

# CLASSES =====================================================================
class UsernameGenerator:
    def __init__(self, names, domain=None):
        self.names = names
        self.domain = domain
        self.user_list = []

    def generate(self):
        """Generate usernames based on given names."""
        for name in self.names:
            lower = name.lower()
            self.user_list.append(lower.replace(" ", "."))  # john.doe
            self.user_list.append(lower.replace(" ", "-"))  # john-doe
            self.user_list.append(lower.replace(" ", ""))   # johndoe

            split = lower.split(" ")
            if len(split) < 2:
                continue  # Skip single names

            first_name = split[0]
            last_name = split[-1]
            initial = first_name[0]
            last_initial = last_name[0]

            self.user_list.append(last_name + first_name)  # doejohn
            self.user_list.append(first_name + last_name)  # johndoe
            self.user_list.append(initial + last_name)     # jdoe
            self.user_list.append(last_name + initial)     # doej
            self.user_list.append(first_name + last_initial)  # johnD
            self.user_list.append(f"{initial}.{last_name}")  # j.doe
            self.user_list.append(f"{last_initial}.{first_name}")  # d.john
            self.user_list.append(f"{first_name}.{last_initial}")  # john.d
            self.user_list.append(f"{initial}-{last_name}")  # j-doe
            self.user_list.append(last_name + first_name[:4])  # doejohn (Amazon email format)
            self.user_list.append(first_name)  # john
            self.user_list.append(last_name)   # doe


        # If a domain is provided, append emails
        if self.domain:
            self.user_list.extend([f"{user}@{self.domain}" for user in self.user_list])

    def get_usernames(self):
        """Return the generated usernames."""
        return self.user_list


class ComplexityScore:
    """Class to handle complexity scoring, duplicate removal, and sorting of strings."""

    def __init__(self, strings):
        self.strings = strings  # Stores the list of strings

    def calculate(self, s):
        """Calculate a complexity score for a given string."""
        length_score = len(s)
        uppercase_score = len(re.findall(r'[A-Z]', s)) * 2
        lowercase_score = len(re.findall(r'[a-z]', s)) * 1
        digit_score = len(re.findall(r'\d', s)) * 3
        special_score = len(re.findall(r'[\W_]', s)) * 4
        space_score = s.count(' ') * 2

        # Deduct points for repeated characters
        repeat_score = sum(s.count(char) - 1 for char in set(s)) * -2  

        return (length_score + uppercase_score + lowercase_score +
                digit_score + special_score + space_score - repeat_score)

    def remove_dups_c_sens(self):
        """Removes duplicates while keeping case differences (case-sensitive)."""
        seen = set()
        self.strings = [x for x in self.strings if not (x in seen or seen.add(x))]

    def remove_dups_c_insens(self):
        """Removes duplicates ignoring case differences (case-insensitive)."""
        seen = set()
        result = []
        for item in self.strings:
            lowered = item.lower()
            if lowered not in seen:
                seen.add(lowered)
                result.append(item)
        self.strings = result

    def get_sorted(self):
        """Returns the list sorted by complexity score."""
        return sorted(self.strings, key=lambda s: self.calculate(s))

# MAIN ========================================================================
def main(file_name, sorting_type, generate, domain, decrease):


    with open(file_name, 'r', encoding="utf8") as file:      
        buffer = [line.strip() for line in file]
    
        # First the generation part
        if generate:
            generator = UsernameGenerator(buffer, domain)
            generator.generate()
            buffer = generator.get_usernames()


        # Then we'll sort depending on the flag
        if sorting_type:

            sorting_list = ComplexityScore(buffer)
            
            # Depending on the result of the left shift we know what was the sorting_type value
            if sorting_type == 2:  
                sorting_list.remove_dups_c_sens()
            if sorting_type == 4:
                sorting_list.remove_dups_c_insens()


        # Get stored list with lines and wheights for each. Regardless of the sorting type
        buffer = sorting_list.get_sorted()

    file.close()

    if decrease:
        buffer.reverse()

    print("\n".join(buffer))

# CONSTRUCT ===================================================================
if __name__ == "__main__":

    # Since that is a script, I'll just leave everything within the if __name__.
    parser = argparse.ArgumentParser(description='Prepare list for user spraying.')

    parser.add_argument("-g", "--generate", action="store_true", dest="generate", default=False, help="Generate usernames from input")
    parser.add_argument("-d", "--domain", action="store", type=str, dest="domain", default="", help="In case there is a domain. (only use with -g)")

    parser.add_argument("-s", "--sort", action="store_true", dest="s", default=False, help="Sort by complexity")
    parser.add_argument("-sds", "--sort_dup_sen", action="store_true", dest="sds", default=False, help="Sort by complexity and remove duplicates case sensitive ('This != this')")
    parser.add_argument("-sdi", "--sort_dup_ins", action="store_true", dest="sdi", default=False, help="Sort by complexity and remove duplicates case insensitive ('This == this')")
 
    parser.add_argument("-de", "--decreased", action="store_true", dest="dec", default=False, help="Sort by decreasing complexity")

    parser.add_argument('file', nargs='?', default="", type=str, help='File with list to sort')
    
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print("Error: Could not find that file. Try an absolute path")
        parser.print_help()
        exit(1)
    
    # Validation - I could do this with argparse grouping functions, but the time investment don't seem worth
    # Ensure that at least one of the sorting flags is set or the generation function
    if not (args.s or args.sds or args.sdi or args.generate):
        parser.error("\n\r\tYou must provide at least one of the sorting flags (-s, -sds, -sdi) or the generating functionality(-g).")

    # Ensure that only one sorting flag is set
    sorting_flags = [args.s, args.sds, args.sdi]
    if sum(sorting_flags) > 1:
        parser.error("\n\r\tYou can only provide one sorting flag at a time (-s, -sds, or -sdi).")

    # If -g is used, -d is optional but allowed
    if args.generate and not args.domain:
        print("Note: You have provided the -g flag but no domain. You can optionally specify a domain with -d.")
    
    binary_value = 0
    for bit in sorting_flags:   # What is life without a left shift? 
        binary_value = (binary_value << 1) | bit  # sorting flags is of the form [0,1,0]. We are treating as if binary 010 = 2

    # Call to main. Where the real logic is. 
    main(args.file, binary_value, args.generate, args.domain, args.dec)
