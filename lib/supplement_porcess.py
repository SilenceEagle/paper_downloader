"""
    supplement_process.py
"""
from PyPDF3 import PdfFileMerger
import zipfile
import os
import shutil
from tqdm import tqdm

def unzipfile(zip_file, save_path):
    """
    unzip zip file to save_path
    :param zipfile: str, zip file's full pathname.
    :param save_path: str, the path store unzipped files.
    :return: None
    """
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(save_path)
    zip_ref.close()


def get_potential_supp_pdf(path):
    """
    get all the potential supplemental pdf file pathname
    :param path: str, the path of unzipped files
    :return: supp_pdf_list, List of str, pdf files' full pathnames
    """
    supp_pdf_list = [f for f in os.scandir(path) if f.name.endswith('.pdf')]
    if len(supp_pdf_list) == 0:
        supp_pdf_list = []
        for dir in os.scandir(path):
            if dir.is_dir() and not dir.name.startswith('__'):
                for pdf in os.scandir(dir.path):
                    if pdf.name.endswith('.pdf'):
                        supp_pdf_list.append(pdf.path)
    if len(supp_pdf_list) == 0:
        supp_pdf_list = []
        for dir in os.scandir(path):
            if dir.is_dir() and not dir.name.startswith('__'):
                for sub_dir in os.scandir(dir):
                    if sub_dir.is_dir() and not sub_dir.name.startswith('__'):
                        for pdf in os.scandir(sub_dir.path):
                            if pdf.name.endswith('.pdf'):
                                supp_pdf_list.append(pdf.path)
    return supp_pdf_list


def move_main_and_supplement_2_one_directory_with_group(main_path, supplement_path, supp_pdf_save_path):
    """
    unzip supplemental zip files to get the pdf files, copy and
        rename them into given path(supp_pdf_save_path/group_name)
    :param main_path: str, the main papers' path
    :param supplement_path: str, the supplemental material 's path
    :param supp_pdf_save_path: str, the supplemental pdf files' save path
    """
    if not os.path.exists(main_path):
        raise ValueError(f'''can not open '{main_path}' !''')
    if not os.path.exists(supplement_path):
        raise ValueError(f'''can not open '{supplement_path}' !''')
    error_log = []
    # make temp dir to unzip zip file
    temp_zip_dir = '.\\temp_zip'
    if not os.path.exists(temp_zip_dir):
        os.mkdir(temp_zip_dir)
    else:
        # remove all files
        for unzip_file in os.listdir(temp_zip_dir):
            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                os.remove(os.path.join(temp_zip_dir, unzip_file))
            if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
            else:
                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
    for group in os.scandir(main_path):
        if group.is_dir():
            paper_bar = tqdm(os.scandir(group.path))
            for paper in paper_bar:
                if paper.is_file():
                    name, extension = os.path.splitext(paper.name)
                    if '.pdf' == extension:
                        paper_bar.set_description(f'''processing {name}''')
                        supp_pdf_path = None
                        # error_flag = False
                        if os.path.exists(os.path.join(supplement_path, group.name, f'{name}_supp.pdf')):
                            supp_pdf_path = os.path.join(supplement_path, group.name,  f'{name}_supp.pdf')
                            shutil.copyfile(
                                supp_pdf_path, os.path.join(supp_pdf_save_path, group.name,  f'{name}_supp.pdf'))
                        elif os.path.exists(os.path.join(supplement_path, group.name, f'{name}_supp.zip')):
                            try:
                                unzipfile(
                                    zip_file=os.path.join(supplement_path, group.name, f'{name}_supp.zip'),
                                    save_path=temp_zip_dir
                                )
                            except Exception as e:
                                print('Error: ' + name + ' - ' + str(e))
                                error_log.append((paper.path, supp_pdf_path, str(e)))
                            try:
                                # find if there is a pdf file (by listing all files in the dir)
                                supp_pdf_list = get_potential_supp_pdf(temp_zip_dir)
                                # rename the first pdf file
                                if len(supp_pdf_list) >= 1:
                                    # by default, we only deal with the first pdf
                                    supp_pdf_path = os.path.join(supp_pdf_save_path, group.name, name+'_supp.pdf')
                                    if not os.path.exists(supp_pdf_path):
                                        shutil.move(supp_pdf_list[0], supp_pdf_path)
                                    if len(supp_pdf_list) > 1:
                                        for i in range(1, len(supp_pdf_list)):
                                            supp_pdf_path = os.path.join(
                                                supp_pdf_save_path, group.name, name + f'_supp_{i}.pdf')
                                            if not os.path.exists(supp_pdf_path):
                                                shutil.move(supp_pdf_list[i], supp_pdf_path)
                                # empty the temp_folder (both the dirs and files)
                                for unzip_file in os.listdir(temp_zip_dir):
                                    if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                        os.remove(os.path.join(temp_zip_dir, unzip_file))
                                    elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                        shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                                    else:
                                        print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                            except Exception as e:
                                print('Error: ' + name + ' - ' + str(e))
                                error_log.append((paper.path, supp_pdf_path, str(e)))

    # 2. write error log
    print('write error log')
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'merge_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is None:
                    f.write('None')
                else:
                    f.write(e)
                f.write('\n')

            f.write('\n')


def move_main_and_supplement_2_one_directory(main_path, supplement_path, supp_pdf_save_path):
    """
    unzip supplemental zip files to get the pdf files, copy and
    rename them into given path(supp_pdf_save_path)
    :param main_path: str, the main papers' path
    :param supplement_path: str, the supplemental material's path
    :param supp_pdf_save_path: str, the supplemental pdf files' save path
    """
    if not os.path.exists(main_path):
        raise ValueError(f'''can not open '{main_path}' !''')
    if not os.path.exists(supplement_path):
        raise ValueError(f'''can not open '{supplement_path}' !''')
    os.makedirs(supp_pdf_save_path, exist_ok=True)
    error_log = []
    # make temp dir to unzip zip file
    temp_zip_dir = '..\\temp_zip'
    if not os.path.exists(temp_zip_dir):
        os.mkdir(temp_zip_dir)
    else:
        # remove all files
        for unzip_file in os.listdir(temp_zip_dir):
            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                os.remove(os.path.join(temp_zip_dir, unzip_file))
            if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
            else:
                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))

    paper_bar = tqdm(os.scandir(main_path))
    for paper in paper_bar:
        if paper.is_file():
            name, extension = os.path.splitext(paper.name)
            if '.pdf' == extension:
                paper_bar.set_description(f'''processing {name}''')
                supp_pdf_path = None
                # error_flag = False
                if os.path.exists(os.path.join(supp_pdf_save_path, f'{name}_supp.pdf')):
                    continue
                elif os.path.exists(os.path.join(supplement_path, f'{name}_supp.pdf')):
                    supp_pdf_path = os.path.join(supplement_path, f'{name}_supp.pdf')
                    shutil.copyfile(supp_pdf_path, os.path.join(supp_pdf_save_path, f'{name}_supp.pdf'))
                elif os.path.exists(os.path.join(supplement_path, f'{name}_supp.zip')):
                    try:
                        unzipfile(
                            zip_file=os.path.join(supplement_path, f'{name}_supp.zip'),
                            save_path=temp_zip_dir)
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                    try:
                        # find if there is a pdf file (by listing all files in the dir)
                        supp_pdf_list = get_potential_supp_pdf(temp_zip_dir)

                        # rename the first pdf file
                        if len(supp_pdf_list) >= 1:
                            # by default, we only deal with the first pdf
                            supp_pdf_path = os.path.join(supp_pdf_save_path, name+'_supp.pdf')
                            if not os.path.exists(supp_pdf_path):
                                shutil.move(supp_pdf_list[0], supp_pdf_path)
                            if len(supp_pdf_list) > 1:
                                for i in range(1, len(supp_pdf_list)):
                                    supp_pdf_path = os.path.join(supp_pdf_save_path, name + f'_supp_{i}.pdf')
                                    if not os.path.exists(supp_pdf_path):
                                        shutil.move(supp_pdf_list[i], supp_pdf_path)
                        # empty the temp_folder (both the dirs and files)
                        for unzip_file in os.listdir(temp_zip_dir):
                            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                os.remove(os.path.join(temp_zip_dir, unzip_file))
                            elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                            else:
                                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))

    # 2. write error log
    print('write error log')
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'merge_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is None:
                    f.write('None')
                else:
                    f.write(e)
                f.write('\n')

            f.write('\n')


def merge_main_supplement(main_path, supplement_path, save_path, is_delete_ori_files=False):
    """
    merge the main paper and supplemental material into one single pdf file
    :param main_path: str, the main papers' path
    :param supplement_path: str, the supplemental material 's path
    :param save_path: str, merged pdf files's save path
    :param is_delete_ori_files: Bool, True for deleting the original main and supplemental material after merging
    """
    if not os.path.exists(main_path):
        raise ValueError(f'''can not open '{main_path}' !''')
    if not os.path.exists(supplement_path):
        raise ValueError(f'''can not open '{supplement_path}' !''')
    os.makedirs(save_path, exist_ok=True)
    error_log = []
    # make temp dir to unzip zip file
    temp_zip_dir = '.\\temp_zip'
    if not os.path.exists(temp_zip_dir):
        os.mkdir(temp_zip_dir)
    else:
        # remove all files
        for unzip_file in os.listdir(temp_zip_dir):
            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                os.remove(os.path.join(temp_zip_dir, unzip_file))
            if os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
            else:
                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
    paper_bar = tqdm(os.scandir(main_path))
    for paper in paper_bar:
        if paper.is_file():
            name, extension = os.path.splitext(paper.name)
            if '.pdf' == extension:
                paper_bar.set_description(f'''processing {name}''')
                if os.path.exists(os.path.join(save_path, paper.name)):
                    continue
                supp_pdf_path = None
                error_floa = False
                if os.path.exists(os.path.join(supplement_path, f'{name}_supp.pdf')):
                    supp_pdf_path = os.path.join(supplement_path, f'{name}_supp.pdf')
                elif os.path.exists(os.path.join(supplement_path, f'{name}_supp.zip')):
                    try:
                        unzipfile(
                            zip_file=os.path.join(supplement_path, f'{name}_supp.zip'),
                            save_path=temp_zip_dir
                        )
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                    try:
                        # find if there is a pdf file (by listing all files in the dir)
                        supp_pdf_list = get_potential_supp_pdf(temp_zip_dir)
                        # rename the first pdf file
                        if len(supp_pdf_list) >= 1:
                            # by default, we only deal with the first pdf
                            supp_pdf_path = os.path.join(supplement_path, name+'_supp.pdf')
                            if not os.path.exists(supp_pdf_path):
                                shutil.move(supp_pdf_list[0], supp_pdf_path)
                        # empty the temp_folder (both the dirs and files)
                        for unzip_file in os.listdir(temp_zip_dir):
                            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                os.remove(os.path.join(temp_zip_dir, unzip_file))
                            elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                            else:
                                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                    except Exception as e:
                        error_floa = True
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                        # empty the temp_folder (both the dirs and files)
                        for unzip_file in os.listdir(temp_zip_dir):
                            if os.path.isfile(os.path.join(temp_zip_dir, unzip_file)):
                                os.remove(os.path.join(temp_zip_dir, unzip_file))
                            elif os.path.isdir(os.path.join(temp_zip_dir, unzip_file)):
                                shutil.rmtree(os.path.join(temp_zip_dir, unzip_file))
                            else:
                                print('Cannot Remove - ' + os.path.join(temp_zip_dir, unzip_file))
                        continue
                if supp_pdf_path is not None:
                    try:
                        merger = PdfFileMerger()
                        f_handle1 = open(paper.path, 'rb')
                        merger.append(f_handle1)
                        f_handle2 = open(supp_pdf_path, 'rb')
                        merger.append(f_handle2)
                        with open(os.path.join(save_path, paper.name), 'wb') as fout:
                            merger.write(fout)
                            print('\tmerged!')
                        f_handle1.close()
                        f_handle2.close()
                        merger.close()
                        if is_delete_ori_files:
                            os.remove(paper.path)
                            if os.path.exists(os.path.join(supplement_path, f'{name}_supp.zip')):
                                os.remove(os.path.join(supplement_path, f'{name}_supp.zip'))
                            if os.path.exists(os.path.join(supplement_path, f'{name}_supp.pdf')):
                                os.remove(os.path.join(supplement_path, f'{name}_supp.pdf'))
                    except Exception as e:
                        print('Error: ' + name + ' - ' + str(e))
                        error_log.append((paper.path, supp_pdf_path, str(e)))
                        if os.path.exists(os.path.join(save_path, paper.name)):
                            os.remove(os.path.join(save_path, paper.name))

                else:
                    if is_delete_ori_files:
                        shutil.move(paper.path, os.path.join(save_path, paper.name))
                    else:
                        shutil.copyfile(paper.path, os.path.join(save_path, paper.name))

    # 2. write error log
    print('write error log')
    project_root_folder = os.path.abspath(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file_pathname = os.path.join(
        project_root_folder, 'log', 'merge_err_log.txt'
    )
    with open(log_file_pathname, 'w') as f:
        for log in tqdm(error_log):
            for e in log:
                if e is None:
                    f.write('None')
                else:
                    f.write(e)
                f.write('\n')

            f.write('\n')


def rename_2_short_name(src_path, save_path, target_max_length=128,
                        extension='pdf'):
    """
    rename file to short filename while remain the conference postfix
    Args:
        src_path (str): path that contains files directly.
        save_path (str): path to save the renamed files.
        target_max_length (int): max filen name length after renaming. All the
            files whose name length is not less than this will be renamed, the
            others will stay unchanged and copy into the save path. Default:
            128.
        extension (str | None): only the files with this extension will be
            processed. None means all file will be processed. Default: 'pdf'.
    Returns:
        None
    """
    if not os.path.exists(src_path):
        raise ValueError(f'Path not found: {src_path}!')

    os.makedirs(save_path, exist_ok=True)

    for f in tqdm(os.scandir(src_path)):
        f_name = f.name

        # compare extension
        ext = os.path.splitext(f_name)[1]
        if extension is not None and ext[1:] != extension:
            continue
        # compare file name length
        l = len(f_name)
        if l < target_max_length:
            if not os.path.exists(os.path.join(save_path, f_name)):
                print(f'\ncopying {f_name}')
                shutil.copyfile(f.path, os.path.join(save_path, f_name))
        else:
            # rename
            try:
                [title, postfix] = f_name.split('_', 1)  # only split to 2 parts
                new_title = title[:target_max_length-len(postfix)-2]
                new_name = f'{new_title}_{postfix}'
                if not os.path.exists(os.path.join(save_path, new_name)):
                    print(f'\nrenaming {f_name} \n\t-> {new_name}')
                    shutil.copyfile(f.path, os.path.join(save_path, new_name))
            except ValueError:
                # ValueError: not enough values to unpack (expected 2, got 1)
                print(f'\nWARNING!!!:\n\tunable to parse postfix from {f.path}')
                print('\tSo, it will be just copy/rename to short name')
                new_title = f_name[:target_max_length - len(ext) - 1]
                new_name = f'{new_title}{ext}'
                if not os.path.exists(os.path.join(save_path, new_name)):
                    print(f'\nrenaming {f_name} \n\t-> {new_name}')
                    shutil.copyfile(f.path, os.path.join(save_path, new_name))


def rename_2_short_name_within_group(src_path, save_path, target_max_length=128,
                        extension='pdf'):
    """
    rename file to short filename while remain the conference postfix
    Args:
        src_path (str): path that contains files:
            src_path/group_name/files
        save_path (str): path to save the renamed files.
        target_max_length (int): max filen name length after renaming. All the
            files whose name length is not less than this will be renamed, the
            others will stay unchanged and copy into the save path. Default:
            128.
        extension (str | None): only the files with this extension will be
            processed. None means all file will be processed. Default: 'pdf'.
    Returns:
        None
    """
    if not os.path.exists(src_path):
        raise ValueError(f'Path not found: {src_path}!')

    os.makedirs(save_path, exist_ok=True)

    for d in tqdm(os.scandir(src_path)):
        if not d.is_dir():
            continue
        print(f'\nprocessing {d.name}')
        d_name = d.name
        d_name = d_name[:min(len(d_name), target_max_length-1)]
        rename_2_short_name(
            src_path=d.path,
            save_path=os.path.join(save_path, d_name),
            target_max_length=target_max_length,
            extension=extension
        )

